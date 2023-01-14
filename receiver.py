#!/usr/bin/env python3
import argparse
import asyncio
import ipaddress
import logging
import time
import someip.header
from someip.sd import SOMEIPDatagramProtocol
import pandas as pd
import matplotlib.pyplot as plt

LOG = logging.getLogger("someip.get")

dt_data_received = []
start_time = time.time()
start_time_data_received = time.time()
class Prot(SOMEIPDatagramProtocol):
    # def __init__(self):
    #     self.pre_time = time.time()

    def get(self, service, method, major_version):
        hdr = someip.header.SOMEIPHeader(
            service_id=service,
            method_id=method,
            client_id=0,
            session_id=0,
            interface_version=major_version,
            message_type=someip.header.SOMEIPMessageType.REQUEST,
        )
        self.send(hdr.build())


    def message_received(
        self,
        someip_message: someip.header.SOMEIPHeader,
        addr: someip.header._T_SOCKNAME,
        multicast: bool,
    ) -> None:
        global start_time_data_received
        dt = time.time() - start_time_data_received
        start_time_data_received = time.time()
        dt_data_received.append(dt * 1000)
        if (time.time() - start_time) >= (5 * 60):
            print(dt_data_received)
            logfilename_tcp_rx = "lidar_rx_dt_" + str(time.time_ns()) + ".log"
            with open(logfilename_tcp_rx, "a") as log1:
                log1.write("lidar_ndn_" + "\n")
                for ii in range(1, int(len(dt_data_received))):
                    log1.write(str(dt_data_received[ii]) + "\n")
                log1.close()
            frames_plt = list(range(0, len(dt_data_received[5:])))
            frames_plt = [x / 1000 for x in frames_plt]

            plt.figure(figsize=(10, 8))
            plt.subplot(1, 2, 1)
            plt.scatter(frames_plt, dt_data_received[5:])
            plt.xlabel('NDN Data Packet Number (in thousands)')
            plt.ylabel('Delta time (in ms): Received LiDAR bytes over NDN Data Packets')

            plt.subplot(1, 2, 2)
            plt.boxplot(dt_data_received[5:])
            plt.savefig("Lidar_dt_data_tx_box_" + str(time.time_ns()) + ".png")
            print("Data RX Ended...going to sleep")
            dt_data_received_pd = pd.DataFrame(dt_data_received[1:])
            logfilename_lidar_rx_summ = "summ_Lidar_rx_dt_" + str(time.time_ns()) + ".log"
            with open(logfilename_lidar_rx_summ, "a") as log2:
                log2.write("Summ_lidar_RX_dt" + "\n")
                log2.write(str(dt_data_received_pd.describe()) + "\n")
                log2.close()
            print(dt_data_received_pd.describe())
            print(len(someip_message.payload))
            time.sleep(1000)


        LOG.info(
            "response: %r / %r", someip_message.return_code, someip_message.payload
        )
        






async def run(addr, port, service, method, version, interval):
    transport, prot = await Prot.create_unicast_endpoint(remote_addr=(str(addr), port))

    try:
        while True:
            prot.get(service, method, version)
            await asyncio.sleep(1 / 1000)
    except asyncio.CancelledError:
        pass
    finally:
        transport.close()


def auto_int(s):
    return int(s, 0)


def setup_log(fmt="", **kwargs):
    try:
        import coloredlogs  # type: ignore[import]
        coloredlogs.install(fmt="%(asctime)s,%(msecs)03d " + fmt, **kwargs)
    except ModuleNotFoundError:
        logging.basicConfig(format="%(asctime)s " + fmt, **kwargs)
        logging.info("install coloredlogs for colored logs :-)")


def main():
    setup_log("%(levelname)-8s %(name)s: %(message)s", level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("host", type=ipaddress.ip_address)
    parser.add_argument("port", type=int)
    parser.add_argument("service", type=auto_int)
    parser.add_argument("method", type=auto_int)
    parser.add_argument("version", type=auto_int)
    parser.add_argument("--interval", type=int, default=3)

    args = parser.parse_args()

    try:
        asyncio.get_event_loop().run_until_complete(
            run(
                args.host,
                args.port,
                args.service,
                args.method,
                args.version,
                args.interval,
            )
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
