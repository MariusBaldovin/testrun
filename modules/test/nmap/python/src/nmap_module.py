# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""NMAP test module"""
import time
import util
import json
import threading
import xmltodict
from test_module import TestModule

LOG_NAME = "test_nmap"
LOGGER = None


class NmapModule(TestModule):
  """NMAP Test module"""

  def __init__(self, module):
    super().__init__(module_name=module, log_name=LOG_NAME)
    self._scan_tcp_results = None
    self._udp_tcp_results = None
    self._scan_results = {}

    global LOGGER
    LOGGER = self._get_logger()

    self._run_nmap()

  def _run_nmap(self):
    LOGGER.info("Running nmap module")

    # Run the monitor method asynchronously to keep this method non-blocking
    self._tcp_scan_thread = threading.Thread(target=self._scan_tcp_ports)
    self._udp_scan_thread = threading.Thread(target=self._scan_udp_ports)

    self._tcp_scan_thread.daemon = True
    self._udp_scan_thread.daemon = True

    self._tcp_scan_thread.start()
    self._udp_scan_thread.start()

    while (self._tcp_scan_thread.is_alive() or
           self._udp_scan_thread.is_alive()):
      time.sleep(1)

    LOGGER.debug("TCP scan results: " + str(self._scan_tcp_results))
    LOGGER.debug("UDP scan results: " + str(self._scan_udp_results))

    self._process_port_results()

  def _process_port_results(self):

    if self._scan_tcp_results is not None:
      self._scan_results.update(self._scan_tcp_results)
    if self._scan_udp_results is not None:
      self._scan_results.update(self._scan_udp_results)

  def _scan_tcp_ports(self):
    max_port = 1000
    LOGGER.info("Running nmap TCP port scan")
    nmap_results = util.run_command(
        f"""nmap --open -sT -sV -Pn -v -p 1-{max_port}
      --version-intensity 7 -T4 -oX - {self._ipv4_addr}""")[0]

    LOGGER.info("TCP port scan complete")
    nmap_results_json = self._nmap_results_to_json(nmap_results)
    self._scan_tcp_results = self._process_nmap_json_results(
        nmap_results_json=nmap_results_json)

  def _scan_udp_ports(self):

    ports = []

    for test in self._get_tests():
      if "config" not in test:
        continue
      test_config = test["config"]
      if "ports" not in test_config:
        continue

      for port in test_config["ports"]:
        if port["type"] == "udp":
          ports.append(str(port["number"]))

    if len(ports) > 0:
      port_list = ",".join(ports)
      LOGGER.info("Running nmap UDP port scan")
      LOGGER.debug("UDP ports: " + str(port_list))
      nmap_results = util.run_command(
          f"nmap -sU -sV -p {port_list} -oX - {self._ipv4_addr}")[0]
      LOGGER.info("UDP port scan complete")
      nmap_results_json = self._nmap_results_to_json(nmap_results)
      self._scan_udp_results = self._process_nmap_json_results(
          nmap_results_json=nmap_results_json)

  def _nmap_results_to_json(self, nmap_results):
    try:
      xml_data = xmltodict.parse(nmap_results)
      json_data = json.dumps(xml_data, indent=4)
      return json.loads(json_data)

    except Exception as e:
      LOGGER.error(f"Error parsing Nmap output: {e}")

  def _process_nmap_json_results(self, nmap_results_json):
    results = {}
    if "host" not in nmap_results_json["nmaprun"]:
      return results
    if "ports" in nmap_results_json["nmaprun"]["host"]:
      ports = nmap_results_json["nmaprun"]["host"]["ports"]
      # Checking if an object is a JSON object
      if isinstance(ports["port"], dict):
        results.update(self._json_port_to_dict(ports["port"]))
      elif isinstance(ports["port"], list):
        for port in ports["port"]:
          results.update(self._json_port_to_dict(port))
    print(str(results))
    return results

  def _json_port_to_dict(self, port_json):
    port_result = {}
    port = {}
    port["number"] = port_json["@portid"]
    port["tcp_udp"] = port_json["@protocol"]
    port["state"] = port_json["state"]["@state"]
    port["service"] = port_json["service"]["@name"]
    port["version"] = ""
    if "@version" in port_json["service"]:
      port["version"] += port_json["service"]["@version"]
    if "@extrainfo" in port_json["service"]:
      port["version"] += " " + port_json["service"]["@extrainfo"]
    port_result = {port_json["@portid"] + port["tcp_udp"]:port}
    return port_result

  def _check_results(self, ports, services):

    LOGGER.info("Checking results")

    match_ports = []

    for open_port, open_port_info in self._scan_results.items():

      for port in ports:
        allowed = True if "allowed" in port and port["allowed"] else False
        if (int(open_port_info["number"]) == int(port["number"]) and
            open_port_info["tcp_udp"] == port["type"] and
            open_port_info["state"] == "open"):
          LOGGER.debug("Found open port: " + str(port["number"]) +
                       "/" + open_port_info["tcp_udp"] +
                       " = " + open_port_info["state"])
          if not allowed:
            match_ports.append(open_port_info["number"] + "/" +
                             open_port_info["tcp_udp"])

      if (open_port_info["service"] in services and
          (open_port_info["number"] + "/" + open_port_info["tcp_udp"]
           ) not in match_ports and
          open_port_info["state"] == "open"):
        LOGGER.debug("Found service " + open_port_info["service"] +
                    " on port " + str(open_port) + "/" +
                    open_port_info["tcp_udp"])
        if not allowed:
          match_ports.append(open_port_info["number"] + "/" +
                            open_port_info["tcp_udp"])

    return match_ports

  def _security_services_ftp(self, config):
    LOGGER.info("Running security.services.ftp")

    open_ports = self._check_results(config["ports"], config["services"])
    if len(open_ports) == 0:
      return True, "No FTP server found"
    else:
      return False, f"Found FTP server running on port {', '.join(open_ports)}"

  def _security_services_telnet(self, config):
    LOGGER.info("Running security.services.telnet")

    open_ports = self._check_results(config["ports"], config["services"])
    if len(open_ports) == 0:
      return True, "No telnet server found"
    else:
      return False, f"Found telnet server running on port {', '.join(open_ports)}"

  def _security_services_smtp(self, config):
    LOGGER.info("Running security.services.smtp")

    open_ports = self._check_results(config["ports"], config["services"])
    if len(open_ports) == 0:
      return True, "No SMTP server found"
    else:
      return False, f"Found SMTP server running on port {', '.join(open_ports)}"

  def _security_services_http(self, config):
    LOGGER.info("Running security.services.http")

    open_ports = self._check_results(config["ports"], config["services"])
    if len(open_ports) == 0:
      return True, "No HTTP server found"
    else:
      return False, f"Found HTTP server running on port {', '.join(open_ports)}"

  def _security_services_pop(self, config):
    LOGGER.info("Running security.services.pop")

    open_ports = self._check_results(config["ports"], config["services"])
    if len(open_ports) == 0:
      return True, "No POP server found"
    else:
      return False, f"Found POP server running on port {', '.join(open_ports)}"

  def _security_services_imap(self, config):
    LOGGER.info("Running security.services.imap")

    open_ports = self._check_results(config["ports"], config["services"])
    if len(open_ports) == 0:
      return True, "No IMAP server found"
    else:
      return False, f"Found IMAP server running on port {', '.join(open_ports)}"

  def _security_services_snmpv3(self, config):
    LOGGER.info("Running security.services.snmpv3")

    open_ports = self._check_results(config["ports"], config["services"])
    if len(open_ports) == 0:
      return True, "No SNMP server found"
    else:
      return False, f"Found SNMP server running on port {', '.join(open_ports)}"

  def _security_services_vnc(self, config):
    LOGGER.info("Running ntp.services.vnc")

    open_ports = self._check_results(config["ports"], config["services"])
    if len(open_ports) == 0:
      return True, "No VNC server found"
    else:
      return False, f"Found VNC server running on port {', '.join(open_ports)}"

  def _security_services_tftp(self, config):
    LOGGER.info("Running security.services.tftp")

    open_ports = self._check_results(config["ports"], config["services"])
    if len(open_ports) == 0:
      return True, "No TFTP server found"
    else:
      return False, f"Found TFTP server running on port {', '.join(open_ports)}"

  def _ntp_network_ntp_server(self, config):
    LOGGER.info("Running ntp.network.ntp_server")

    open_ports = self._check_results(config["ports"], config["services"])
    if len(open_ports) == 0:
      return True, "No NTP server found"
    else:
      return False, f"Found NTP server running on port {', '.join(open_ports)}"

  def _security_ssh_version(self, config):
    LOGGER.info("Running security.ssh.version")

    open_ports = self._check_results(config["ports"], config["services"])
    if len(open_ports) == 0:
      return True, "No SSH server found"
    else:
      # Perform version check
      for open_port, open_port_info in self._scan_results.items():
        if ((open_port == 22 or open_port_info["service"] == "ssh") and
            open_port_info["state"] == "open"):
          if config["version"] in open_port_info["version"]:
            return True, f"SSH server found running {open_port_info['version']}"
          else:
            return False, f"SSH server found running {open_port_info['version']}"
