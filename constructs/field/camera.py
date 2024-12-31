from construct import Adapter, Padding, Struct
from construct import Int16ul, Int16sl, Int32sl
from dataclasses import dataclass
from globals import Vertex3

@dataclass
class Camera:
    axis_x: Vertex3
    axis_y: Vertex3
    axis_z: Vertex3
    pos: Vertex3
    zoom: int

    @property
    def tx(self):
        return -((self.pos.x * self.axis_x.x) + (self.pos.y * self.axis_y.x) + (self.pos.z * self.axis_z.x))

    @property
    def ty(self):
        return -((self.pos.x * self.axis_x.y) + (self.pos.y * self.axis_y.y) + (self.pos.z * self.axis_z.y))

    @property
    def tz(self):
        return -((self.pos.x * self.axis_x.z) + (self.pos.y * self.axis_y.z) + (self.pos.z * self.axis_z.z))

class CameraAdapter(Adapter):
    def _decode(self, obj, context, path):
        vx=Vertex3((obj.camera_vector_x.x / 4096),(obj.camera_vector_x.y / 4096), (obj.camera_vector_x.z / 4096))
        vy=Vertex3(-(obj.camera_vector_y.x / 4096),-(obj.camera_vector_y.y / 4096), -(obj.camera_vector_y.z / 4096))
        vz=Vertex3((obj.camera_vector_z.x / 4096),(obj.camera_vector_z.y / 4096), (obj.camera_vector_z.z / 4096))
        vp = Vertex3((obj.camera_pos.x / 4096), -(obj.camera_pos.y / 4096), (obj.camera_pos.z / 4096))
        return Camera(vx,vy,vz,vp ,obj.zoom)

CameraConstruct = CameraAdapter(Struct(
    "camera_vector_x" / Struct("x" / Int16sl, "y" / Int16sl, "z" / Int16sl),
    "camera_vector_y" / Struct("x" / Int16sl, "y" / Int16sl, "z" / Int16sl),
    "camera_vector_z" / Struct("x" / Int16sl, "y" / Int16sl, "z" / Int16sl),
    Padding(2),
    "camera_pos" / Struct("x" / Int32sl, "y" / Int32sl, "z" / Int32sl),
    Padding(4),
    "zoom" / Int16ul
))