"""Test pushbullet integration."""

from unittest.mock import MagicMock, patch

from pushover_complete import BadAPIRequestError
import pytest
import requests_mock
from urllib3.exceptions import MaxRetryError

from homeassistant.components.pushover.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from . import MOCK_CONFIG

from tests.common import MockConfigEntry


@pytest.fixture(autouse=False)
def mock_pushover():
    """Mock pushover."""
    with patch(
        "pushover_complete.PushoverAPI._generic_post", return_value={}
    ) as mock_generic_post:
        yield mock_generic_post


async def test_async_setup_entry_success(
    hass: HomeAssistant, mock_pushover: MagicMock
) -> None:
    """Test pushover successful setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED


@pytest.mark.usefixtures("mock_pushover")
@pytest.mark.parametrize(
    ("data", "service"),
    [
        pytest.param(MOCK_CONFIG, "pushover_work", id="entry_title"),
        pytest.param(
            {**MOCK_CONFIG, CONF_NAME: "Legacy name"}, "legacy_name", id="stored_name"
        ),
    ],
)
async def test_notify_service_name(
    hass: HomeAssistant, data: dict[str, str], service: str
) -> None:
    """Test the notify service is named after a stored name or the entry title."""
    entry = MockConfigEntry(domain=DOMAIN, title="Pushover Work", data=data)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.services.has_service("notify", service)


async def test_unique_id_updated(hass: HomeAssistant, mock_pushover: MagicMock) -> None:
    """Test updating unique_id to new format."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, unique_id="MYUSERKEY")
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert entry.unique_id is None


async def test_async_setup_entry_failed_invalid_api_key(
    hass: HomeAssistant, mock_pushover: MagicMock
) -> None:
    """Test pushover failed setup due to invalid api key."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    mock_pushover.side_effect = BadAPIRequestError("400: application token is invalid")
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_async_setup_entry_failed_conn_error(
    hass: HomeAssistant, mock_pushover: MagicMock
) -> None:
    """Test pushover failed setup due to conn error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    mock_pushover.side_effect = BadAPIRequestError
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_async_setup_entry_failed_json_error(
    hass: HomeAssistant, requests_mock: requests_mock.Mocker
) -> None:
    """Test pushover failed setup due to bad json response from library."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    requests_mock.post(
        "https://api.pushover.net/1/users/validate.json", status_code=204
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_async_setup_entry_failed_urrlib3_error(
    hass: HomeAssistant, mock_pushover: MagicMock
) -> None:
    """Test pushover failed setup due to conn error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    mock_pushover.side_effect = MaxRetryError(MagicMock(), MagicMock())
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY
