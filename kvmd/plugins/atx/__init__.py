# ========================================================================== #
#                                                                            #
#    KVMD - The main PiKVM daemon.                                           #
#                                                                            #
#    Copyright (C) 2018-2024  Maxim Devaev <mdevaev@gmail.com>               #
#                                                                            #
#    This program is free software: you can redistribute it and/or modify    #
#    it under the terms of the GNU General Public License as published by    #
#    the Free Software Foundation, either version 3 of the License, or       #
#    (at your option) any later version.                                     #
#                                                                            #
#    This program is distributed in the hope that it will be useful,         #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of          #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           #
#    GNU General Public License for more details.                            #
#                                                                            #
#    You should have received a copy of the GNU General Public License       #
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.  #
#                                                                            #
# ========================================================================== #


from typing import AsyncGenerator

from ...errors import OperationError
from ...errors import IsBusyError

from .. import BasePlugin
from .. import get_plugin_class
from ...logging import get_logger

import asyncio

# =====
class AtxError(Exception):
    pass


class AtxOperationError(OperationError, AtxError):
    pass


class AtxIsBusyError(IsBusyError, AtxError):
    def __init__(self) -> None:
        super().__init__("Performing another ATX operation, please try again later")


# =====
class BaseAtx(BasePlugin):
    async def get_state(self) -> dict:
        raise NotImplementedError

    async def trigger_state(self) -> None:
        raise NotImplementedError

    async def poll_state(self) -> AsyncGenerator[dict, None]:
        # ==== Granularity table ====
        #   - enabled -- Full
        #   - busy    -- Partial
        #   - leds    -- Partial
        # ===========================

        yield {}
        raise NotImplementedError

    async def cleanup(self) -> None:
        pass

    # =====

    async def _run_script(self, action: str, wait: bool) -> None:
        cmd = ["/etc/kvmd/atx/atx.sh", action]
        process = await asyncio.create_subprocess_exec(*cmd)
        if wait:
            await process.wait()
            if process.returncode != 0:
                raise AtxOperationError(f"Script execution failed for action: {action}")

    async def power_on(self, wait: bool) -> None:
        await self.click_power(wait)

    async def power_off(self, wait: bool) -> None:
        await self.click_power(wait)

    async def power_off_hard(self, wait: bool) -> None:
        await self.click_power_long(wait)

    async def power_reset_hard(self, wait: bool) -> None:
        await self.click_reset(wait)

    # =====

    async def click_power(self, wait: bool) -> None:
         await self._run_script("short", wait)
         get_logger(0).info("Click power short")

    async def click_power_long(self, wait: bool) -> None:
        await self._run_script("long", wait)
        get_logger(0).info("Click power long")

    async def click_reset(self, wait: bool) -> None:
        await self._run_script("reset", wait)
        get_logger(0).info("Click reset")

# =====
def get_atx_class(name: str) -> type[BaseAtx]:
    return get_plugin_class("atx", name)  # type: ignore
