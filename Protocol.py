from construct import *
from construct.lib import *
from binascii import hexlify, unhexlify

class XorEncrypted(SymmetricAdapter):
    """Optionally xor-encrypted."""
    __slots__ = ['key']
    def __init__(self, subcon, key):
        super(XorEncrypted, self).__init__(subcon)
        self.key = key
    def _decode(self, obj, context):
        if context.has_key('encrypted') and context.encrypted:
            key = self.key * (1 + len(obj) // len(self.key))
            obj = ''.join(chr(ord(a) ^ ord(b)) for a,b in zip(obj, key))
        return obj

def PasswordString(subcon, key):
    return XorEncrypted(subcon, key)

Password = Struct('password' / PasswordString(GreedyBytes, 'NtgrSmartSwitchRock'))
MacAddress = ExprAdapter(Byte[6],
                         encoder = lambda obj, ctx: [int(octet, 16) for octet in obj.split(':')],
                         decoder = lambda obj, ctx: ':'.join('%02x' % b for b in obj))
IPv4Address = ExprAdapter(Byte[4],
                          encoder = lambda obj, ctx: [int(octet) for octet in obj.split('.')],
                          decoder = lambda obj, ctx: '.'.join('%d' % b for b in obj))
MAC = Optional(Struct('address' / MacAddress))
IPv4 = Optional(Struct('address' / IPv4Address))
PortsByte = ExprAdapter(Byte,
                        encoder = lambda obj, ctx: sum([1 << (7 - p) for p in xrange(0, 8) if (p + 1) in obj]),
                        decoder = lambda obj, ctx: [p + 1 for p in xrange(0, 8) if obj & (1 << (7 - p))])
TLVBitmap = Optional(Struct('unknown' / Int, Embedded(BitStruct('unknown_0' / Flag,
                                                                'unknown_1' / Flag,
                                                                'unknown_2' / Flag,
                                                                'unknown_3' / Flag,

                                                                'multicast_0' / Flag,
                                                                'multicast_1' / Flag,
                                                                'multicast_2' / Flag,
                                                                'vlan_0' / Flag,

                                                                'unknown_8' / Flag,
                                                                'port_mirroring' / Flag,
                                                                'broadcast_filtering_0' / Flag,
                                                                'broadcast_filtering_1' / Flag,

                                                                'rate_limit_0' / Flag,
                                                                'rate_limit_1' / Flag,
                                                                'unknown_14' / Flag,
                                                                'unknown_15' / Flag,

                                                                'unknown_16' / Flag,
                                                                'qos_0' / Flag,
                                                                'qos_1' / Flag,
                                                                'qos_2' / Flag,

                                                                'vlan_1' / Flag,
                                                                'vlan_2' / Flag,
                                                                'vlan_3' / Flag,
                                                                'vlan_port' / Flag,

                                                                'unknown_24' / Flag,
                                                                'unknown_25' / Flag,
                                                                'cable_test' / Flag,
                                                                'port_statistics' / Flag,

                                                                'unknown_28' / Flag,
                                                                'unknown_29' / Flag,
                                                                'unknown_30' / Flag,
                                                                'factory_reset' / Flag))))
TLVBitmap = Optional(Struct('unknown' / Int, Embedded(BitStruct('tlv' / Flag[32]))))
Unknown = Struct('unknown' / GreedyBytes)
LinkSpeedEnum = Enum(Byte,
                     speed_0 = 0,
                     speed_10m_hd = 1,
                     speed_10m_fd = 2,
                     speed_100m_hd = 3,
                     speed_100m_fd = 4,
                     speed_1000m = 5,
                     speed_10g = 6)
CableStatusEnum = Enum(Int,
                       ok = 0,
                       no_cable = 1,
                       open_cable = 2,
                       short_circuit = 3,
                       fiber_cable = 4,
                       shorted_cable = 5,
                       unknown = 6,
                       crosstalk = 7)
PortLimit = Optional(Struct('port' / Byte,
                            'limit' / Enum(Int,
                                           none=0,
                                           k512=1,
                                           m1=2,
                                           m2=3,
                                           m4=4,
                                           m8=5,
                                           m16=6,
                                           m32=7,
                                           m64=8,
                                           m128=9,
                                           m256=10,
                                           m512=11)))
BroadcastFilteringEnabled = Optional(Struct('enabled' / ExprAdapter(Byte,
                                        encoder = lambda o, c: o == 0x03,
                                        decoder = lambda o, c: '\x03' if o else '\x00')))

Message = 'message' / Struct(
    'tag' / Enum(Short,
                 # Information
                 product_name             = 0x0001,
                 product_type             = 0x0002, # guess
                 system_name              = 0x0003,
                 mac_address              = 0x0004,
                 location                 = 0x0005, # guess
                 ip_address               = 0x0006,
                 netmask                  = 0x0007,
                 gateway                  = 0x0008,
                 change_password          = 0x0009,
                 password                 = 0x000a,
                 dhcp                     = 0x000b,
                 firmware_images          = 0x000c, # guess
                 firmware_version         = 0x000d,
                 firmware_version2        = 0x000e, # guess
                 firmware_active_image    = 0x000f, # guess
                 password_encryption      = 0x0014,
                 link_speed               = 0x0c00,
                 port_traffic_stats       = 0x1000,
                 cable_test_result        = 0x1c00,
                 vlan                     = 0x2000,
                 vlan_id                  = 0x2400,
                 vlan_id_802_1q           = 0x2800,
                 vlan_pvid                = 0x3000,
                 qos                      = 0x3400,
                 port_qos                 = 0x3800,
                 port_ingress             = 0x4c00,
                 port_engress             = 0x5000,
                 broadcast_filtering      = 0x5400,
                 port_broadcast_bandwidth = 0x5800,
                 port_mirroring           = 0x5c00,
                 number_of_ports          = 0x6000,
                 igmp_snooping            = 0x6800,
                 block_unknown_multicasts = 0x6c00,
                 igmp_header_validation   = 0x7000,
                 tlv_bitmap               = 0x7400,
                 loop_detection           = 0x9000,

                 # Actions
                 firmware_upgrade         = 0x0010,
                 reboot                   = 0x0013,
                 factory_reset            = 0x0400,
                 reset_port_traffic_stats = 0x1400,
                 test_cable               = 0x1800,
                 delete_vlan_id_802_1q    = 0x2c00,

                 # Messages with unknown meaning
                 unknown0017              = 0x0017, # This message is sent by the ProSAFE Plus Utility before changing password.
                 unknown6400              = 0x6400,
                 unknown7c00              = 0x7c00,
                 unknown8000              = 0x8000,
                 unknown8800              = 0x8800,
                 unknown8c00              = 0x8c00,
                 unknown9400              = 0x9400,

                 # End of messages-marker
                 end_of_messages          = 0xffff),
    Embedded(Prefixed(Short, Switch(this.tag, {
        'product_name':              Optional(Struct('name' / GreedyBytes)),
        'product_type':              Unknown,
        'system_name':               Optional(Struct('name' / GreedyBytes)),
        'location':                  Struct('location' / GreedyBytes),
        'mac_address':               MAC,
        'ip_address':                IPv4,
        'netmask':                   IPv4,
        'gateway':                   IPv4,
        'change_password':           Password,
        'password':                  Password,
        'dhcp':                      Optional(Struct('enabled' / Flag)),
        'firmware_images':           Optional(Struct('images' / Byte)),
        'firmware_version':          Optional(Struct('version' / GreedyBytes)),
        'firmware_version2':         Unknown,
        'firmware_active_image':     Optional(Struct('image' / Byte)),
        'password_encryption':       Optional(Struct('enabled' / Flag)),
        'link_speed':                Optional(Struct('port' / Byte, 'speed' / LinkSpeedEnum, Const('\x01'))),
        'port_traffic_stats':        Optional(Struct('port' / Byte, 'received' / Long, 'sent' / Long, Default(Long[3], [0, 0, 0]), 'crc_errors' / Long)),
        'cable_test_result':         Optional(Struct('port' / Byte, Embedded(Optional(Struct('status' / CableStatusEnum, 'meters' / Int))))),
        'vlan':                      Optional(Struct('type' / Enum(Byte, none=0, basic_port=1, advanced_port=2, basic_802_1q=3, advanced_802_1q=4))),
        'vlan_id':                   Optional(Struct('vlanid' / Short, Embedded(Optional(Struct('member_ports' / PortsByte))))),
        'vlan_id_802_1q':            Optional(Struct('vlanid' / Short, Embedded(Optional(Struct('tagged_ports' / PortsByte, 'member_ports' / PortsByte))))),
        'vlan_pvid':                 Optional(Struct('port' / Byte, 'vlanid' / Short)),
        'qos':                       Optional(Struct('type' / Enum(Byte, port=1, dscp=2))),
        'port_qos':                  Optional(Struct('port' / Byte, 'priority' / Enum(Byte, high=1, medium=2, normal=3, low=4))),
        'port_ingress':              PortLimit,
        'port_engress':              PortLimit,
        'broadcast_filtering':       BroadcastFilteringEnabled,
        'port_broadcast_bandwidth':  PortLimit,
        'port_mirroring':            Optional(Struct('destination_port' / Byte, Default(Byte, 0), 'source_ports' / PortsByte)),
        'number_of_ports':           Optional(Struct('ports' / Byte)),
        'igmp_snooping':             Optional(Struct('enabled' / Flag, 'vlanid' / Short)),
        'block_unknown_multicasts':  Optional(Struct('enabled' / Flag)),
        'igmp_header_validation':    Optional(Struct('enabled' / Flag)),
        'tlv_bitmap':                TLVBitmap,
        'loop_detection':            Optional(Struct('enabled' / Flag)),
        'firmware_upgrade':          Struct(Default(Byte, 1)),
        'reboot':                    Struct(Default(Byte, 1)),
        'factory_reset':             Struct(Default(Byte, 1)),
        'reset_port_traffic_stats':  Struct(Default(Byte, 1)),
        'test_cable':                Struct('port' / Byte, Default(Byte, 1)),
        'delete_vlan_id_802_1q':     Struct('vlanid' / Short),
        'unknown0017':               Unknown,
        'unknown6400':               Unknown,
        'unknown7c00':               Unknown,
        'unknown8000':               Unknown,
        'unknown8800':               Unknown,
        'unknown8c00':               Unknown,
        'unknown9400':               Unknown,
        'end_of_messages':           Pass,
    })))
)

Packet = 'packet' / Struct(
    'version' / Byte,
    'operation' / Enum(Byte,
                       read_req = 1,
                       read_rsp = 2,
                       write_req = 3,
                       write_rsp = 4),
    'result' / Enum(Byte,
                    success                     = 0x00,
                    protocol_version_mismatch   = 0x01,
                    command_not_supported       = 0x02,
                    tlv_not_supported           = 0x03,
                    tlv_length_error            = 0x04,
                    tlv_value_error             = 0x05,
                    ip_not_allowed              = 0x06,
                    incorrect_password          = 0x07,
                    boot_code_firmware_download = 0x08,
                    incorrect_username          = 0x09,
                    configure_via_web           = 0x0a,
                    tftp_call_error             = 0x0c,
                    incorrect_password2         = 0x0d,
                    auth_failed_lock            = 0x0e,
                    management_disabled         = 0x0f,
                    tftp_call_error2            = 0x81,
                    tftp_out_of_memory          = 0x82,
                    firmware_upgrade_failed     = 0x83,
                    tftp_timeout                = 0x84,
                    command_scheduled           = 0xf0,
                    command_in_progress         = 0xf1,
                    tftp_in_progress            = 0xf2,
                    internal_error              = 0xf8,
                    timeout                     = 0xff),
    'unknown_0' / Default(Byte, 0),
    'unknown_1' / Default(Int, 0),
    'host_mac' / MacAddress,
    'device_mac' / MacAddress,
    'unknown_2' / Default(Short, 0),
    'sequence' / Short,
    Const(b'NSDP'),
    'unknown_3' / Default(Int, 0),
    'messages' / RepeatUntil(lambda obj, lst, ctx: obj.tag == 'end_of_messages', Message)
)

data = unhexlify('01 01 0000 00000000 080027da96d7 000000000000 0000 0001 4e534450 00000000 0014 0000 6000 0001 08 0c00 0000 0c00 0003 020201 1000 0000 1000 0031 03 0000000100000000 0000000002000000 0000000000000000 0000000000000000 0000000000000000 0000000000000005 1c00 0000 1c00 0009 04 00000003 00000011 2800 0000 2800 0004 0001 80 9f ffff 0000'.replace(' ', ''))
p = Packet.parse(data)

Packet.build(p)