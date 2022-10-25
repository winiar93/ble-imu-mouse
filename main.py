import uasyncio as asyncio
from machine import SoftSPI, Pin, I2C
import time
from hid_services import Mouse

from lsm6dsox import LSM6DSOX
import machine

machine.freq(240000000)

lsm = LSM6DSOX(I2C(0, scl=Pin(13), sda=Pin(12)))
right_button = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_UP)
left_button = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)

class Device:
    def __init__(self, name="BLE IMU MOUSE"):
        # Define state
        self.axes = (0, 0)
        self.updated = False
        self.active = True

#         # Define buttons
#         self.pin_forward = Pin(5, Pin.IN)
#         self.pin_reverse = Pin(23, Pin.IN)
#         self.pin_right = Pin(19, Pin.IN)
#         self.pin_left = Pin(18, Pin.IN)

        # Create our device
        self.mouse = Mouse(name)
        # Set a callback function to catch changes of device state
        self.mouse.set_state_change_callback(self.mouse_state_callback)

    # Function that catches device status events
    def mouse_state_callback(self):
        if self.mouse.get_state() is Mouse.DEVICE_IDLE:
            return
        elif self.mouse.get_state() is Mouse.DEVICE_ADVERTISING:
            return
        elif self.mouse.get_state() is Mouse.DEVICE_CONNECTED:
            return
        else:
            return

    def advertise(self):
        self.mouse.start_advertising()

    def stop_advertise(self):
        self.mouse.stop_advertising()

    async def advertise_for(self, seconds=30):
        self.advertise()

        while seconds > 0 and self.mouse.get_state() is Mouse.DEVICE_ADVERTISING:
            await asyncio.sleep(1)
            seconds -= 1

        if self.mouse.get_state() is Mouse.DEVICE_ADVERTISING:
            self.stop_advertise()

#     # Input loop
#     async def gather_input(self):
#         while self.active:
#             prevaxes = self.axes
#             self.axes = (self.pin_right.value() * 127 - self.pin_left.value() * 127, self.pin_forward.value() * 127 - self.pin_reverse.value() * 127)
#             self.updated = self.updated or not (prevaxes == self.axes)  # If updated is still True, we haven't notified yet
#             await asyncio.sleep_ms(50)

    # Bluetooth device loop
    async def notify(self):
        while self.active:
            # If connected, set axes and notify
            # If idle, start advertising for 30s or until connected
            if self.updated:
                if self.mouse.get_state() is Mouse.DEVICE_CONNECTED:
                    self.mouse.set_axes(self.axes[0], self.axes[1])
                    self.mouse.notify_hid_report()
                elif self.mouse.get_state() is Mouse.DEVICE_IDLE:
                    await self.advertise_for(30)
                self.updated = False

            if self.mouse.get_state() is Mouse.DEVICE_CONNECTED:
                await asyncio.sleep_ms(50)
            else:
                await asyncio.sleep(2)

    async def co_start(self):
        # Start our device
        if self.mouse.get_state() is Mouse.DEVICE_STOPPED:
            self.mouse.start()
            self.active = True
            #await asyncio.gather(self.advertise_for(30), self.gather_input(), self.notify())
            await asyncio.gather(self.advertise_for(30), self.notify())

    async def co_stop(self):
        self.active = False
        self.mouse.stop()

    def start(self):
        asyncio.run(self.co_start())

    def stop(self):
        asyncio.run(self.co_stop())

    # Test routine
    async def test(self):
        while not self.mouse.is_connected():
            await asyncio.sleep(5)

        await asyncio.sleep(5)
        self.mouse.set_battery_level(50)
        self.mouse.notify_battery_level()
        await asyncio.sleep_ms(500)
        
        gx_data = []
        gy_data = []
        
        while True:
            try:
                #ax, ay, az = lsm.read_accel()
                gx, gy, gz = lsm.read_gyro()
            except:
                pass
            
            gy_value = -int(gz)
            gx_value = int(gy)
            
            if len(gx_data) < 10 and len(gy_data) < 10:
            
                gy_data.append(gy_value)
                gx_data.append(gx_value)
            
            else:
                # Mooving average method to smooth imu readings
                gy_data.pop(0)
                gx_data.pop(0)
                gy_data.append(gy_value)
                gx_data.append(gx_value)
                
                new_mouse_y_position = int(sum(gy_data)/10)
                new_mouse_x_position = int(sum(gx_data)/10)
                
                dead_zone = 4
# uncomment if need to define dead zone of movment            
#             if new_mouse_y_position < -dead_zone or dead_zone < new_mouse_y_position:
#                 new_mouse_y_position = new_mouse_y_position
#             else:
#                 new_mouse_y_position = 0
#                 
#             if new_mouse_x_position < -dead_zone or dead_zone < new_mouse_x_position:
#                 new_mouse_x_position = new_mouse_x_position
#             else:
#                 new_mouse_x_position = 0

                #reverse button value readings
                swap = {0: 1, 1:0}
                
                self.mouse.set_buttons(b2=swap[right_button.value()],b1=swap[left_button.value()])
                await asyncio.sleep_ms(5)
                
                self.mouse.set_axes(new_mouse_y_position, new_mouse_x_position)
                self.mouse.notify_hid_report()
                await asyncio.sleep_ms(25)
            
#         self.mouse.set_buttons()
#         self.mouse.notify_hid_report()
#         await asyncio.sleep_ms(500)
# 
#         self.mouse.set_battery_level(100)
#         self.mouse.notify_battery_level()

    async def co_start_test(self):
        self.mouse.start()
        await asyncio.gather(self.advertise_for(30), self.test())

    # start test
    def start_test(self):
        asyncio.run(self.co_start_test())

if __name__ == "__main__":
    d = Device()
    d.start_test()