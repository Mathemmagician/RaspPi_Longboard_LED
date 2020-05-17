#!/usr/bin/python
import smbus2
import math


class Gyroscope(object):
    """This class is used to interact with MPU6050 Gyroscope"""

    power_mgmt_1 = 0x6b
    power_mgmt_2 = 0x6c

    def __init__(self, address=0x68):
        'Find Address via running `i2cdetect -y 1` in console. 0x68 by default'
        self.bus = smbus2.SMBus(1)
        self.address = address

        self.bus.write_byte_data(address, self.power_mgmt_1, 0)

    # Information Read Methods
    def read_byte(self, reg):
        return self.bus.read_byte_data(self.address, reg)

    def read_word(self, reg):
        h = self.bus.read_byte_data(self.address, reg)
        l = self.bus.read_byte_data(self.address, reg+1)
        value = (h << 8) + l
        return value

    def read_word_2c(self, reg):
        val = self.read_word(reg)
        if (val >= 0x8000):
            return -((65535 - val) + 1)
        else:
            return val


    # Math Methods
    @classmethod
    def dist(cls, a,b):
        return math.sqrt(a*a + b*b)

    @classmethod
    def get_x_rotation(cls, x,y,z):
        radians = math.atan2(y, cls.dist(x,z))
        return math.degrees(radians)

    @classmethod
    def get_y_rotation(cls, x,y,z):
        ''' Originally:
        radians = math.atan2(x, cls.dist(y,z))
        return -math.degrees(radians)
        '''
        radians = -math.atan2(x, cls.dist(y,z))
        return math.degrees(radians)

    @classmethod
    def get_z_rotation(cls, x,y,z):
        'Note the assymmetry in formula' 
        radians = math.atan2(cls.dist(y,x), z)
        return math.degrees(radians)

    def get_xyz_rotation_radians(self):
        'Returns a dictionary of acc-s in radians. Optimize in future'
        x,y,z = self.get_xyz_acceleration()

        radx = math.atan2(y, self.dist(x,z))
        rady = -math.atan2(x, self.dist(y,z))
        radz = math.atan2(self.dist(y,x), z)
        return {'x': radx, 'y': rady, 'z': radz}

    def xyz_out(self):
        gyro_xout = self.read_word_2c(0x43)
        gyro_yout = self.read_word_2c(0x45)
        gyro_zout = self.read_word_2c(0x47)
        return gyro_xout, gyro_yout, gyro_zout

    def get_xyz_acceleration(self): 
        '''
            Returns scalled xyz accelerations
            Can be also interpreted as the normal vector
            Note: when perpendicular, z rotation is impossible to find
        '''
        acceleration_xout = self.read_word_2c(0x3b)
        acceleration_yout = self.read_word_2c(0x3d)
        acceleration_zout = self.read_word_2c(0x3f)
        
        xacc_scaled = acceleration_xout / 16384.0
        yacc_scaled = acceleration_yout / 16384.0
        zacc_scaled = acceleration_zout / 16384.0

        return (xacc_scaled, yacc_scaled, zacc_scaled)

    def get_xyz_rotation(self):
        '''
            x range: [-90, 90]
            y range: [-90, 90]
            z range: [0,  180]
        '''
        accelerations = self.get_xyz_acceleration()
        xrot = self.get_x_rotation(*accelerations)
        yrot = self.get_y_rotation(*accelerations)
        zrot = self.get_z_rotation(*accelerations)
        return (xrot, yrot, zrot)


if __name__ == '__main__': 
    from time import sleep

    print(" Testing gyroscope", "\n===========================")

    print(" Initializing gyroscope ")
    g = Gyroscope()
    while True:
        #print(" Printing xy rotation:", g.xy_rotation())
        #print(" xyz_acc ", *g.get_xyz_rotation(), sep='\t')
        print(" xyz_acc ", *g.get_xyz_acceleration(), sep='\t')
        sleep(0.3)

