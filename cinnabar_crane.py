#!/usr/bin/env python3
"""Cinnabar Crane — neon ingot-stacker arcade for ElbowOS. Python 3 + pygame."""

import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/CINNABAR_CRANE_ElbowOS.mp4")
INK, WINE = (14, 5, 8), (48, 12, 20)
VERM, GOLD, COPPER = (232, 54, 46), (255, 196, 72), (214, 108, 52)
ROSE, TEAL, CREAM = (255, 126, 142), (72, 240, 206), (255, 236, 220)
EMBER, ASH = (255, 150, 54), (90, 28, 32)
COLS = [VERM, GOLD, COPPER, ROSE, (255, 92, 64), (255, 214, 120)]


class Game:
    def __init__(self, seed=11):
        random.seed(seed)
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY and not RECORD else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            self.screen = pygame.Surface((W, H))
        pygame.display.set_caption("Cinnabar Crane")
        self.font = pygame.font.SysFont("dejavusans", 64, bold=True)
        self.mid = pygame.font.SysFont("dejavusans", 36, bold=True)
        self.small = pygame.font.SysFont("dejavusans", 28, bold=True)
        self.reset()

    def reset(self):
        self.t = 0.0
        self.score = 0
        self.combo = 0
        self.lives = 3
        self.cam = 0.0
        self.blocks = [{"x": -280, "y": 0, "w": 560, "h": 78, "c": COPPER}]
        self.crane = 0.0
        self.cv = 0.0
        self.hold_w = 480
        self.fall = None
        self.scraps = []
        self.sparks = []
        self.embers = [
            [random.uniform(40, W - 40), random.uniform(200, H - 80), random.uniform(40, 140)]
            for _ in range(48)
        ]
        self.drop_cd = 0.45
        self.flash = 0.0
        self.banner = "DROP THE HOOK"
        self.keys = set()

    def top(self):
        return self.blocks[-1]

    def step(self, dt, auto=False):
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        self.drop_cd = max(0.0, self.drop_cd - dt)
        for e in self.embers:
            e[1] -= e[2] * dt
            e[0] += math.sin(self.t * 2 + e[2]) * 18 * dt
            if e[1] < 160:
                e[1] = H - 70
                e[0] = random.uniform(40, W - 40)
        if auto:
            self._auto(dt)
        else:
            if pygame.K_LEFT in self.keys or pygame.K_a in self.keys:
                self.cv -= 2400 * dt
            if pygame.K_RIGHT in self.keys or pygame.K_d in self.keys:
                self.cv += 2400 * dt
        self.cv *= 0.90
        self.crane = max(-430, min(430, self.crane + self.cv * dt))
        if self.fall:
            self.fall["vy"] += 2800 * dt
            self.fall["y"] += self.fall["vy"] * dt
            top = self.top()
            if self.fall["y"] <= top["y"] + top["h"]:
                self._land()
        for s in self.scraps:
            s["vy"] -= 1400 * dt
            s["y"] += s["vy"] * dt
            s["x"] += s["vx"] * dt
            s["rot"] += s["vr"] * dt
            s["life"] -= dt
        self.scraps = [s for s in self.scraps if s["life"] > 0]
        for p in self.sparks:
            p["y"] += p["vy"] * dt
            p["x"] += p["vx"] * dt
            p["life"] -= dt
        self.sparks = [p for p in self.sparks if p["life"] > 0]
        goal = self.top()["y"] + self.top()["h"]
        self.cam += (goal - self.cam) * min(1.0, 4.5 * dt)

    def _auto(self, dt):
        top = self.top()
        target = top["x"] + top["w"] * 0.5 + math.sin(self.t * 1.7) * 36
        # a late nudge so a few drops shear instead of sitting perfect
        if self.drop_cd < 0.12:
            target += math.sin(self.t * 9.0) * 70
        self.cv += max(-1, min(1, (target - self.crane) / 80)) * 2200 * dt
        if self.fall is None and self.drop_cd <= 0 and abs(self.crane - target) < 46:
            self._release()

    def _release(self):
        if self.fall is not None:
            return
        top = self.top()
        w = min(self.hold_w, top["w"] + 40)
        self.fall = {
            "x": self.crane - w / 2,
            "y": self.cam + 620,
            "w": w,
            "h": 72,
            "vy": 40,
            "c": COLS[len(self.blocks) % len(COLS)],
        }
        self.drop_cd = 0.62

    def _land(self):
        f, top = self.fall, self.top()
        left = max(f["x"], top["x"])
        right = min(f["x"] + f["w"], top["x"] + top["w"])
        overlap = right - left
        self.fall = None
        if overlap < 46:
            self.combo = 0
            self.lives -= 1
            self.banner = "SLAG OFF"
            self.flash = 0.35
            self.scraps.append(
                {"x": f["x"], "y": f["y"], "w": f["w"], "h": f["h"], "c": f["c"],
                 "vx": random.choice([-280, 280]), "vy": 220, "rot": 0, "vr": 4, "life": 0.8}
            )
            if self.lives <= 0:
                self.score = max(self.score, 0)
                self.reset()
                self.banner = "KILN REFIRE"
            return
        overhang_l = left - f["x"]
        overhang_r = (f["x"] + f["w"]) - right
        block = {"x": left, "y": top["y"] + top["h"], "w": overlap, "h": 72, "c": f["c"]}
        self.blocks.append(block)
        perfect = overhang_l < 18 and overhang_r < 18
        self.combo = self.combo + 1 if perfect else 1
        gain = int(overlap / 8) + (40 * self.combo if perfect else 0)
        self.score += gain
        self.banner = "PERFECT POUR" if perfect else "SHEARED"
        self.flash = 0.22
        self.hold_w = max(180, overlap - (0 if perfect else 8))
        for side, ow in (("L", overhang_l), ("R", overhang_r)):
            if ow > 8:
                sx = f["x"] if side == "L" else right
                self.scraps.append(
                    {"x": sx, "y": block["y"], "w": ow, "h": 72, "c": f["c"],
                     "vx": -340 if side == "L" else 340, "vy": 80, "rot": 0,
                     "vr": -5 if side == "L" else 5, "life": 0.7}
                )
        for _ in range(14):
            self.sparks.append(
                {"x": left + random.random() * overlap, "y": block["y"] + 72,
                 "vx": random.uniform(-180, 180), "vy": random.uniform(80, 360),
                 "life": random.uniform(0.25, 0.6), "c": random.choice([GOLD, TEAL, CREAM])}
            )

    def _sy(self, wy):
        return 1180 - (wy - self.cam)

    def draw(self, surf):
        surf.fill(INK)
        # kiln brick columns
        for i in range(12):
            x = 36 + i * 90
            shade = 28 + (i % 3) * 8
            pygame.draw.rect(surf, (shade, 8, 14), (x, 150, 70, H - 230), border_radius=6)
            for k in range(18):
                yy = 180 + k * 92 - int(self.cam * 0.15) % 92
                pygame.draw.line(surf, (60, 16, 24), (x, yy), (x + 70, yy), 2)
        for e in self.embers:
            pygame.draw.circle(surf, EMBER, (int(e[0]), int(e[1])), 3)
        # stacked ingots
        for b in self.blocks[-16:]:
            sy = self._sy(b["y"] + b["h"])
            if sy > H + 40 or sy < 80:
                continue
            rect = pygame.Rect(int(W / 2 + b["x"]), int(sy), int(b["w"]), int(b["h"]))
            pygame.draw.rect(surf, b["c"], rect, border_radius=10)
            hi = tuple(min(255, c + 70) for c in b["c"])
            pygame.draw.rect(surf, hi, (rect.x + 8, rect.y + 8, rect.w - 16, 14), border_radius=6)
            pygame.draw.rect(surf, (40, 8, 10), rect, 3, border_radius=10)
        if self.fall:
            f = self.fall
            sy = self._sy(f["y"] + f["h"])
            rect = pygame.Rect(int(W / 2 + f["x"]), int(sy), int(f["w"]), int(f["h"]))
            pygame.draw.rect(surf, f["c"], rect, border_radius=10)
            pygame.draw.rect(surf, CREAM, rect, 3, border_radius=10)
        for s in self.scraps:
            sy = self._sy(s["y"] + s["h"])
            chip = pygame.Surface((max(2, int(s["w"])), int(s["h"])), pygame.SRCALPHA)
            chip.fill((*s["c"], 230))
            rot = pygame.transform.rotate(chip, s["rot"] * 40)
            surf.blit(rot, rot.get_rect(center=(int(W / 2 + s["x"] + s["w"] / 2), int(sy + 36))))
        for p in self.sparks:
            sy = self._sy(p["y"])
            pygame.draw.circle(surf, p["c"], (int(W / 2 + p["x"]), int(sy)), 4)
        # crane rail + hook
        pygame.draw.rect(surf, (70, 22, 28), (40, 250, W - 80, 18), border_radius=8)
        hx = int(W / 2 + self.crane)
        pygame.draw.rect(surf, GOLD, (hx - 28, 242, 56, 34), border_radius=6)
        pygame.draw.line(surf, TEAL, (hx, 276), (hx, 390), 4)
        pygame.draw.polygon(surf, CREAM, [(hx - 26, 390), (hx + 26, 390), (hx + 16, 418), (hx - 16, 418)])
        if self.fall is None:
            hw = self.hold_w
            ghost = pygame.Rect(hx - hw // 2, 424, hw, 64)
            pygame.draw.rect(surf, (*COLS[len(self.blocks) % len(COLS)],), ghost, border_radius=8)
            pygame.draw.rect(surf, TEAL, ghost, 3, border_radius=8)
        if self.flash > 0:
            veil = pygame.Surface((W, H), pygame.SRCALPHA)
            veil.fill((255, 180, 80, int(90 * self.flash / 0.35)))
            surf.blit(veil, (0, 0))
        title = self.font.render("CINNABAR CRANE", True, GOLD)
        surf.blit(title, title.get_rect(center=(W // 2, 88)))
        score = self.mid.render(f"SCORE  {self.score}", True, CREAM)
        surf.blit(score, (56, 150))
        combo = self.mid.render(f"x{self.combo}  LIVES {self.lives}", True, TEAL)
        surf.blit(combo, combo.get_rect(right=W - 56, top=150))
        tag = self.small.render(self.banner, True, ROSE)
        surf.blit(tag, tag.get_rect(center=(W // 2, 210)))
        foot = self.mid.render("x.com/ElbowOS", True, CREAM)
        bar = pygame.Surface((W, 90), pygame.SRCALPHA)
        bar.fill((12, 4, 8, 180))
        surf.blit(bar, (0, H - 90))
        surf.blit(foot, foot.get_rect(center=(W // 2, H - 46)))

    def play(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = clock.tick(FPS) / 1000
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    self.keys.add(ev.key)
                    if ev.key == pygame.K_SPACE:
                        self._release()
                    if ev.key == pygame.K_r:
                        self.reset()
                elif ev.type == pygame.KEYUP:
                    self.keys.discard(ev.key)
            self.step(dt, auto=False)
            self.draw(self.screen)
            pygame.display.flip()
        pygame.quit()

    def record(self):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "veryfast", "-movflags", "+faststart", OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        n = FPS * SECS
        try:
            for _ in range(n):
                self.step(1 / FPS, auto=True)
                self.draw(self.screen)
                proc.stdin.write(pygame.image.tobytes(self.screen, "RGB"))
        except BrokenPipeError:
            err = proc.stderr.read().decode("utf-8", "ignore")
            raise SystemExit(f"ffmpeg pipe broke:\n{err[-1500:]}")
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1500:]}")
        print("wrote", OUT)
        pygame.quit()


def main():
    if PLAY and not RECORD:
        Game().play()
        return
    Game(seed=11).record()


if __name__ == "__main__":
    main()
