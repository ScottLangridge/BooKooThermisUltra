class Shot:
    def __init__(self):
        self.g_in = None
        self.g_out = None
        self.time = None

    def completed(self):
        return None not in [self.g_in, self.g_out, self.time]


class ShotLogger:
    def __init__(self, scale):
        self.scale = scale
        assert scale.is_connected(), "Shot Logger expects to be provided with a connected scale"

        self.shot = None

    def init_shot(self):
        self.shot = Shot()

    def log_g_in(self, g_in):
        if not self.shot:
            self.init_shot()
        self.shot.g_in = self.scale.weight

    def run_shot(self):
        self.scale.send_tare_and_timer_start()
        weight = self.scale.read_weight()
        # while weight greater than a quarter second ago:
        #    sleep(0.25)
        self.self.scale.timer_stop()
        self.shot.g_out = weight
        self.shot.time = self.scale.read_time()
