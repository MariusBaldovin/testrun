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
"""TLS test module"""
# pylint: disable=W0212

from test_module import TestModule
from tls_util import TLSUtil
import os
import pyshark
from binascii import hexlify
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, dsa, ec
from cryptography.x509 import AuthorityKeyIdentifier, SubjectKeyIdentifier, BasicConstraints, KeyUsage
from cryptography.x509 import GeneralNames, DNSName, ExtendedKeyUsage, ObjectIdentifier, SubjectAlternativeName

LOG_NAME = 'test_tls'
MODULE_REPORT_FILE_NAME = 'tls_report.html'
STARTUP_CAPTURE_FILE = '/runtime/device/startup.pcap'
MONITOR_CAPTURE_FILE = '/runtime/device/monitor.pcap'
TLS_CAPTURE_FILE = '/runtime/output/tls.pcap'
GATEWAY_CAPTURE_FILE = '/runtime/network/gateway.pcap'
LOGGER = None


class TLSModule(TestModule):
  """The TLS testing module."""

  def __init__(self,
               module,
               log_dir=None,
               conf_file=None,
               results_dir=None,
               startup_capture_file=STARTUP_CAPTURE_FILE,
               monitor_capture_file=MONITOR_CAPTURE_FILE,
               tls_capture_file=TLS_CAPTURE_FILE):
    super().__init__(module_name=module,
                     log_name=LOG_NAME,
                     log_dir=log_dir,
                     conf_file=conf_file,
                     results_dir=results_dir)
    self.startup_capture_file = startup_capture_file
    self.monitor_capture_file = monitor_capture_file
    self.tls_capture_file = tls_capture_file
    global LOGGER
    LOGGER = self._get_logger()
    self._tls_util = TLSUtil(LOGGER)

  def generate_module_report(self):
    html_content = '<h1>TLS Module</h1>'

    # List of capture files to scan
    pcap_files = [
        self.startup_capture_file, self.monitor_capture_file,
        self.tls_capture_file
    ]
    certificates = self.extract_certificates_from_pcap(pcap_files,
                                                       self._device_mac)
    if len(certificates) > 0:

      # Add summary table
      summary_table = '''
        <table class="module-data">
          <thead>
            <tr>
              <th>Expiry</th>
              <th>Length</th>
              <th>Type</th>
              <th>Port number</th>
              <th>Signed by</th>
            </tr>
          </thead>
          <tbody>
        '''

      cert_tables = []
      for cert_num, ((ip_address, port), # pylint: disable=W0612
                     cert) in enumerate(certificates.items()):

        # Extract certificate data
        not_valid_before = cert.not_valid_before
        not_valid_after = cert.not_valid_after
        version_value = f'{cert.version.value + 1} ({hex(cert.version.value)})'
        signature_alg_value = cert.signature_algorithm_oid._name
        not_before = str(not_valid_before)
        not_after = str(not_valid_after)
        public_key = cert.public_key()
        signed_by = 'None'
        if isinstance(public_key, rsa.RSAPublicKey):
          public_key_type = 'RSA'
        elif isinstance(public_key, dsa.DSAPublicKey):
          public_key_type = 'DSA'
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
          public_key_type = 'EC'
        else:
          public_key_type = 'Unknown'
        # Calculate certificate length
        cert_length = len(
            cert.public_bytes(encoding=serialization.Encoding.DER))

        # Generate the Certificate table
        cert_table = f'''
          <h1>Certificate</h1>
          <table class="module-data">
            <thead>
              <tr>
                <th>Property</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Version</td>
                <td>{version_value}</td>
              </tr>
              <tr>
                <td>Signature Alg.</td>
                <td>{signature_alg_value}</td>
              </tr>
              <tr>
                <td>Validity from</td>
                <td>{not_before}</td>
              </tr>
              <tr>
                <td>Valid to</td>
                <td>{not_after}</td>
              </tr>
            </tbody>
          </table>
        '''

        # Generate the Subject table
        subj_table = '''
          <h1>Subject</h1>
          <table class="module-data">
            <thead>
              <tr>
                <th>Distinguished Name</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
        '''

        for val in cert.subject.rdns:
          dn = val.rfc4514_string().split('=')
          subj_table += f'''
            <tr>
              <td>{dn[0]}</td>
              <td>{dn[1]}</td>
            </tr>
          '''
        subj_table += '''
            </tbody>
          </table>
        '''

        # Generate the Subject table
        iss_table = '''
          <h1>Issuer</h1>
          <table class="module-data">
            <thead>
              <tr>
                <th>Distinguished Name</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
        '''

        for val in cert.issuer.rdns:
          dn = val.rfc4514_string().split('=')
          iss_table += f'''
            <tr>
              <td>{dn[0]}</td>
              <td>{dn[1]}</td>
            </tr>
          '''
          if 'CN' in dn[0]:
            signed_by = dn[1]
        iss_table += '''
            </tbody>
          </table>
        '''

        ext_table = None
        if cert.extensions:
          ext_table = '''
            <h1>Extensions</h1>
            <table class="module-data">
                <thead>
                  <tr>
                    <th>Extension</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
            '''

          for extension in cert.extensions:
            if isinstance(extension.value, list):
              for extension_value in extension.value:
                ext_table += f'''
                    <tr>
                      <td>{extension.oid._name}</td> 
                      <td>{self.format_extension_value(extension_value.value)}</td>
                    </tr> 
                  '''
            else:
              ext_table += f'''
                    <tr>
                      <td>{extension.oid._name}</td> 
                      <td>{self.format_extension_value(extension.value)}</td>
                    </tr> 
                  '''
          ext_table += '''
                </tbody>
              </table>
            '''
        cert_table = f'\n{cert_table}'
        cert_table += f'\n\n{subj_table}'
        cert_table += f'\n\n{iss_table}'
        if ext_table is not None:
          cert_table += f'\n\n{ext_table}'
        cert_tables.append(cert_table)

        summary_table += f'''
              <tr>
                <td>{not_after}</td>
                <td>{cert_length}</td>
                <td>{public_key_type}</td>
                <td>{port}</td>
                <td>{signed_by}</td>
              </tr>
            '''

      summary_table += '''
          </tbody>
        </table>
      '''

      html_content += summary_table + '\n'.join('\n' + tables
                                                for tables in cert_tables)

    else:
      html_content += ('''
        <div class="callout-container info">
          <div class="icon"></div>
          No TLS certificates found on the device
        </div>''')

    LOGGER.debug('Module report:\n' + html_content)

    # Use os.path.join to create the complete file path
    report_path = os.path.join(self._results_dir, MODULE_REPORT_FILE_NAME)

    # Write the content to a file
    with open(report_path, 'w', encoding='utf-8') as file:
      file.write(html_content)

    LOGGER.info('Module report generated at: ' + str(report_path))
    return report_path

  def format_extension_value(self, value):
    if isinstance(value, bytes):
      # Convert byte sequences to hex strings
      return hexlify(value).decode()
    elif isinstance(value, (list, tuple)):
      # Format lists/tuples for HTML output
      return ', '.join([self.format_extension_value(v) for v in value])
    elif isinstance(value, ExtendedKeyUsage):
      # Handle ExtendedKeyUsage extension
      return ', '.join(
          [oid._name or f'Unknown OID ({oid.dotted_string})' for oid in value])
    elif isinstance(value, GeneralNames):
      # Handle GeneralNames (used in SubjectAlternativeName)
      return ', '.join(
          [name.value for name in value if isinstance(name, DNSName)])
    elif isinstance(value, SubjectAlternativeName):
      # Extract and format the GeneralNames (which contains DNSName,
      #IPAddress, etc.)
      return self.format_extension_value(value.get_values_for_type(DNSName))

    elif isinstance(value, ObjectIdentifier):
      # Handle ObjectIdentifier directly
      return value._name or f'Unknown OID ({value.dotted_string})'
    elif hasattr(value, '_name'):
      # Extract the name for OIDs (Object Identifiers)
      return value._name
    elif isinstance(value, AuthorityKeyIdentifier):
      # Handle AuthorityKeyIdentifier extension
      key_id = self.format_extension_value(value.key_identifier)
      cert_issuer = value.authority_cert_issuer
      cert_serial = value.authority_cert_serial_number

      return (f'key_identifier={key_id}, '
              f'authority_cert_issuer={cert_issuer}, '
              f'authority_cert_serial_number={cert_serial}')
    elif isinstance(value, SubjectKeyIdentifier):
      # Handle SubjectKeyIdentifier extension
      return f'digest={self.format_extension_value(value.digest)}'
    elif isinstance(value, BasicConstraints):
      # Handle BasicConstraints extension
      return f'ca={value.ca}, path_length={value.path_length}'
    elif isinstance(value, KeyUsage):
      # Handle KeyUsage extension
      return (f'digital_signature={value.digital_signature}, '
              f'key_cert_sign={value.key_cert_sign}, '
              f'key_encipherment={value.key_encipherment}, '
              f'crl_sign={value.crl_sign}')
    return str(value)  # Fallback to string conversion

  def extract_certificates_from_pcap(self, pcap_files, mac_address):
    # Initialize a list to store packets
    all_packets = []
    # Iterate over each file
    for pcap_file in pcap_files:
      # Open the capture file
      packets = pyshark.FileCapture(pcap_file)
      try:
        # Iterate over each packet in the file and add it to the list
        for packet in packets:
          all_packets.append(packet)
      finally:
        # Close the capture file
        packets.close()

    certificates = {}
    # Loop through each item (packet)
    for packet in all_packets:
      if 'TLS' in packet:
        # Check if the packet's source matches the target MAC address
        if 'eth' in packet and (packet.eth.src == mac_address):
          # Look for attribute of x509
          if hasattr(packet['TLS'], 'x509sat_utf8string'):
            certificate_bytes = bytes.fromhex(
                packet['TLS'].handshake_certificate.replace(':', ''))
            # Parse the certificate bytes
            certificate = x509.load_der_x509_certificate(
                certificate_bytes, default_backend())
            # Extract IP address and port from packet
            ip_address = packet.ip.src
            port = packet.tcp.srcport if 'tcp' in packet else packet.udp.srcport
            # Store certificate in dictionary with IP address and port as key
            certificates[(ip_address, port)] = certificate
    return certificates

  def _security_tls_v1_2_server(self):
    LOGGER.info('Running security.tls.v1_2_server')
    self._resolve_device_ip()
    # If the ipv4 address wasn't resolved yet, try again
    if self._device_ipv4_addr is not None:
      tls_1_2_results = self._tls_util.validate_tls_server(
          self._device_ipv4_addr, tls_version='1.2')
      tls_1_3_results = self._tls_util.validate_tls_server(
          self._device_ipv4_addr, tls_version='1.3')
      results = self._tls_util.process_tls_server_results(
          tls_1_2_results, tls_1_3_results)
      # Determine results and return proper messaging and details
      description = ''
      if results[0] is None:
        description = 'TLS 1.2 certificate could not be validated'
      elif results[0]:
        description = 'TLS 1.2 certificate is valid'
      else:
        description = 'TLS 1.2 certificate is invalid'
      return results[0], description, results[1]

    else:
      LOGGER.error('Could not resolve device IP address. Skipping')
      return 'Error', 'Could not resolve device IP address'

  def _security_tls_v1_3_server(self):
    LOGGER.info('Running security.tls.v1_3_server')
    self._resolve_device_ip()
    # If the ipv4 address wasn't resolved yet, try again
    if self._device_ipv4_addr is not None:
      results = self._tls_util.validate_tls_server(self._device_ipv4_addr,
                                                   tls_version='1.3')
      # Determine results and return proper messaging and details
      description = ''
      if results[0] is None:
        description = 'TLS 1.3 certificate could not be validated'
      elif results[0]:
        description = 'TLS 1.3 certificate is valid'
      else:
        description = 'TLS 1.3 certificate is invalid'
      return results[0], description, results[1]

    else:
      LOGGER.error('Could not resolve device IP address')
      return 'Error', 'Could not resolve device IP address'

  def _security_tls_v1_0_client(self):
    LOGGER.info('Running security.tls.v1_0_client')
    self._resolve_device_ip()
    # If the ipv4 address wasn't resolved yet, try again
    if self._device_ipv4_addr is not None:
      tls_1_0_valid = self._validate_tls_client(self._device_ipv4_addr, '1.0')
      tls_1_1_valid = self._validate_tls_client(self._device_ipv4_addr, '1.1')
      tls_1_2_valid = self._validate_tls_client(self._device_ipv4_addr, '1.2')
      tls_1_3_valid = self._validate_tls_client(self._device_ipv4_addr, '1.3')
      states = [
          tls_1_0_valid[0], tls_1_1_valid[0], tls_1_2_valid[0], tls_1_3_valid[0]
      ]
      if any(state is True for state in states):
        # If any state is True, return True
        result_state = True
        result_message = 'TLS 1.0 or higher detected'
      elif all(state == 'Feature Not Detected' for state in states):
        # If all states are "Feature not Detected"
        result_state = 'Feature Not Detected'
        result_message = tls_1_0_valid[1]
      elif all(state == 'Error' for state in states):
        # If all states are "Error"
        result_state = 'Error'
        result_message = ''
      else:
        result_state = False
        result_message = 'TLS 1.0 or higher was not detected'
      result_details = tls_1_0_valid[2] + tls_1_1_valid[2] + tls_1_2_valid[
          2] + tls_1_3_valid[2]
      result_tags = list(
          set(tls_1_0_valid[3] + tls_1_1_valid[3] + tls_1_2_valid[3] +
              tls_1_3_valid[3]))
      return result_state, result_message, result_details, result_tags
    else:
      LOGGER.error('Could not resolve device IP address. Skipping')
      return 'Error', 'Could not resolve device IP address'

  def _security_tls_v1_2_client(self):
    LOGGER.info('Running security.tls.v1_2_client')
    self._resolve_device_ip()
    # If the ipv4 address wasn't resolved yet, try again
    if self._device_ipv4_addr is not None:
      return self._validate_tls_client(self._device_ipv4_addr,
                                       '1.2',
                                       unsupported_versions=['1.0', '1.1'])
    else:
      LOGGER.error('Could not resolve device IP address. Skipping')
      return 'Error', 'Could not resolve device IP address'

  def _security_tls_v1_3_client(self):
    LOGGER.info('Running security.tls.v1_3_client')
    self._resolve_device_ip()
    # If the ipv4 address wasn't resolved yet, try again
    if self._device_ipv4_addr is not None:
      return self._validate_tls_client(self._device_ipv4_addr,
                                       '1.3',
                                       unsupported_versions=['1.0', '1.1'])
    else:
      LOGGER.error('Could not resolve device IP address. Skipping')
      return 'Error', 'Could not resolve device IP address'

  def _validate_tls_client(self,
                           client_ip,
                           tls_version,
                           unsupported_versions=None):
    client_results = self._tls_util.validate_tls_client(
        client_ip=client_ip,
        tls_version=tls_version,
        capture_files=[
            MONITOR_CAPTURE_FILE, STARTUP_CAPTURE_FILE, TLS_CAPTURE_FILE
        ],
        unsupported_versions=unsupported_versions)

    # Generate results based on the state
    result_state = None
    result_message = ''
    result_details = ''
    result_tags = []

    if client_results[0] is not None:
      result_details = client_results[1]
      if client_results[0]:
        result_state = True
        result_message = f'TLS {tls_version} client connections valid'
      else:
        result_state = False
        result_message = f'TLS {tls_version} client connections invalid'
    else:
      result_state = 'Feature Not Detected'
      result_message = 'No outbound connections were found'
    return result_state, result_message, result_details, result_tags

  def _resolve_device_ip(self):
    # If the ipv4 address wasn't resolved yet, try again
    if self._device_ipv4_addr is None:
      self._device_ipv4_addr = self._get_device_ipv4()
