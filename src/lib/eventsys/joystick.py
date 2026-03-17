
class JoystickDriver:
    
    def get_instance_id(self):
        raise NotImplementedError("JoystickDriver.get_instance_id() not implemented")

    def get_numaxes(self):
        raise NotImplementedError("JoystickDriver.get_numaxes() not implemented")

    def get_axis(self, axis):
        raise NotImplementedError("JoystickDriver.get_axis() not implemented")
    
    def get_numballs(self):
        raise NotImplementedError("JoystickDriver.get_numballs() not implemented")
    
    def get_ball(self, ball):
        raise NotImplementedError("JoystickDriver.get_ball() not implemented")
    
    def get_numbuttons(self):
        raise NotImplementedError("JoystickDriver.get_numbuttons() not implemented")
    
    def get_button(self, button):
        raise NotImplementedError("JoystickDriver.get_button() not implemented")
    
    def get_numhats(self):
        raise NotImplementedError("JoystickDriver.get_numhats() not implemented")
    
    def get_hat(self, hat):
        raise NotImplementedError("JoystickDriver.get_hat() not implemented")