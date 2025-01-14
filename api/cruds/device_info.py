from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

import api.models.device_info as device_model
import api.schemas.device_info as device_schema

import subprocess
import re


async def create_device_info(
        db: AsyncSession, device_info_create: device_schema.DeviceInfoCreate
) -> device_model.DeviceInfo:
    device_info = device_model.DeviceInfo(**device_info_create.dict())
    db.add(device_info)
    await db.commit()
    await db.refresh(device_info)
    return device_info


async def get_mac_addresses():
    try:
        # `arp -a` コマンドを実行して、ネットワーク上のデバイスの IP アドレスと MAC アドレスを取得
        result = subprocess.run(['arp', '-a'], stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')

        # 出力結果からMACアドレスを抽出
        mac_addresses = []
        for line in output.splitlines():
            # MAC アドレスは通常、コロン区切りの形式で表示される
            if "at" in line:
                parts = line.split()
                mac_address = parts[3]  # MACアドレスは通常4番目の要素
                mac_addresses.append(mac_address)

        return mac_addresses
    except Exception as e:
        return str(e)