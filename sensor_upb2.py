from uprotobuf import *


@registerMessage
class TimeMessage(Message):
    _proto_fields=[
        dict(name='hour', type=WireType.Varint, subType=VarintSubType.Int32, fieldType=FieldType.Required, id=1),
        dict(name='minute', type=WireType.Varint, subType=VarintSubType.Int32, fieldType=FieldType.Required, id=2),
        dict(name='second', type=WireType.Varint, subType=VarintSubType.Int32, fieldType=FieldType.Required, id=3),
    ]

@registerMessage
class SensordataMessage(Message):
    _proto_fields=[
        dict(name='temprature', type=WireType.Bit32, subType=FixedSubType.Float, fieldType=FieldType.Required, id=1),
        dict(name='publisher_id', type=WireType.Length, subType=LengthSubType.String, fieldType=FieldType.Required, id=2),
        dict(name='timestamp', type=WireType.Length, subType=LengthSubType.Message, fieldType=FieldType.Required, id=3, mType='.Time'),
    ]


