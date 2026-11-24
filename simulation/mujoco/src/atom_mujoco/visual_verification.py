"""Multi-frame acvision candidates. No simulation truth."""
class VisualVerification:
    def __init__(self, source, target, color, dwell=3):
        self.source = (8-int(source[1]), ord(source[0])-ord('a'))
        self.target = (8-int(target[1]), ord(target[0])-ord('a'))
        self.color = {'white': 1, 'black': 2}[color]
        self.dwell = dwell
        self.reset()

    def reset(self):
        self.last_sequence = 0
        self.source_missing = self.target_present = 0
        self.state = 'UNKNOWN'

    def update(self, frame):
        if frame.sequence <= self.last_sequence:
            raise ValueError('Visual verification requires distinct ordered frames')
        self.last_sequence = frame.sequence
        if frame.homography is None or not frame.oriented:
            self.source_missing = self.target_present = 0
            self.state = 'UNKNOWN'
            return self.state
        source, target = frame.candidates[self.source], frame.candidates[self.target]
        self.source_missing = self.source_missing+1 if source == 0 else 0
        self.target_present = self.target_present+1 if target == self.color else 0
        self.state = 'SOURCE_CANDIDATE' if source == self.color else 'UNKNOWN'
        if self.source_missing >= self.dwell:
            self.state = 'SOURCE_APPARENTLY_ABSENT'
        if target == self.color:
            self.state = 'TARGET_CANDIDATE'
        if self.source_missing >= self.dwell and self.target_present >= self.dwell:
            self.state = 'TARGET_TEMPORALLY_PRESENT_CANDIDATE'
        return self.state
