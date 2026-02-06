const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const speedEl = document.getElementById("speed");
const distanceEl = document.getElementById("distance");
const bestEl = document.getElementById("best");
const restartBtn = document.getElementById("restart");

const state = {
  running: true,
  speed: 0,
  baseSpeed: 140,
  boost: 0,
  distance: 0,
  best: Number(localStorage.getItem("neon-sprint-best") || 0),
  laneIndex: 1,
  lanePositions: [110, 210, 310],
  playerX: 210,
  playerY: 500,
  traffic: [],
  roadOffset: 0,
  lastSpawn: 0,
};

const keys = {
  left: false,
  right: false,
  boost: false,
};

const player = {
  width: 50,
  height: 80,
};

function resetGame() {
  state.running = true;
  state.speed = 0;
  state.boost = 0;
  state.distance = 0;
  state.laneIndex = 1;
  state.playerX = state.lanePositions[state.laneIndex];
  state.traffic = [];
  state.roadOffset = 0;
  state.lastSpawn = 0;
}

function spawnTraffic() {
  const lane = Math.floor(Math.random() * state.lanePositions.length);
  const size = 60 + Math.random() * 30;
  state.traffic.push({
    x: state.lanePositions[lane],
    y: -size - 20,
    width: size * 0.7,
    height: size,
    speed: 80 + Math.random() * 80,
    color: `hsl(${200 + Math.random() * 80}, 80%, 60%)`,
  });
}

function handleInput() {
  if (keys.left) {
    state.laneIndex = Math.max(0, state.laneIndex - 1);
    keys.left = false;
  }
  if (keys.right) {
    state.laneIndex = Math.min(state.lanePositions.length - 1, state.laneIndex + 1);
    keys.right = false;
  }
  state.playerX = state.lanePositions[state.laneIndex];
  state.boost = keys.boost ? 80 : 0;
}

function update(delta) {
  if (!state.running) return;

  handleInput();

  const targetSpeed = state.baseSpeed + state.boost;
  state.speed += (targetSpeed - state.speed) * 0.05;
  const meters = (state.speed * delta) / 1000;
  state.distance += meters;

  state.roadOffset += (state.speed * delta) / 120;
  if (state.roadOffset > 80) state.roadOffset = 0;

  state.traffic.forEach((car) => {
    car.y += (state.speed + car.speed) * delta / 1000;
  });

  state.traffic = state.traffic.filter((car) => car.y < canvas.height + 120);

  state.lastSpawn += delta;
  if (state.lastSpawn > 850 - Math.min(state.distance * 4, 500)) {
    spawnTraffic();
    state.lastSpawn = 0;
  }

  detectCollision();

  speedEl.textContent = Math.round(state.speed);
  distanceEl.textContent = Math.round(state.distance);
}

function detectCollision() {
  const playerRect = {
    x: state.playerX - player.width / 2,
    y: state.playerY - player.height / 2,
    width: player.width,
    height: player.height,
  };

  for (const car of state.traffic) {
    const rect = {
      x: car.x - car.width / 2,
      y: car.y - car.height / 2,
      width: car.width,
      height: car.height,
    };

    const overlap =
      playerRect.x < rect.x + rect.width &&
      playerRect.x + playerRect.width > rect.x &&
      playerRect.y < rect.y + rect.height &&
      playerRect.y + playerRect.height > rect.y;

    if (overlap) {
      state.running = false;
      state.best = Math.max(state.best, Math.round(state.distance));
      localStorage.setItem("neon-sprint-best", state.best.toString());
      bestEl.textContent = state.best;
      speedEl.textContent = "0";
      break;
    }
  }
}

function drawRoad() {
  ctx.fillStyle = "#1b1f34";
  ctx.fillRect(60, 0, 300, canvas.height);

  ctx.strokeStyle = "rgba(255,255,255,0.15)";
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(60, 0);
  ctx.lineTo(60, canvas.height);
  ctx.moveTo(360, 0);
  ctx.lineTo(360, canvas.height);
  ctx.stroke();

  ctx.strokeStyle = "rgba(255,255,255,0.35)";
  ctx.lineWidth = 6;
  for (let i = -1; i < 12; i += 1) {
    const y = i * 80 + state.roadOffset;
    ctx.beginPath();
    ctx.moveTo(210, y);
    ctx.lineTo(210, y + 40);
    ctx.stroke();
  }
}

function drawPlayer() {
  ctx.fillStyle = "#39ffcc";
  ctx.beginPath();
  ctx.roundRect(
    state.playerX - player.width / 2,
    state.playerY - player.height / 2,
    player.width,
    player.height,
    12
  );
  ctx.fill();

  ctx.fillStyle = "rgba(0,0,0,0.25)";
  ctx.fillRect(state.playerX - 18, state.playerY + 10, 10, 18);
  ctx.fillRect(state.playerX + 8, state.playerY + 10, 10, 18);
}

function drawTraffic() {
  state.traffic.forEach((car) => {
    ctx.fillStyle = car.color;
    ctx.beginPath();
    ctx.roundRect(
      car.x - car.width / 2,
      car.y - car.height / 2,
      car.width,
      car.height,
      10
    );
    ctx.fill();

    ctx.fillStyle = "rgba(0,0,0,0.2)";
    ctx.fillRect(car.x - car.width / 2 + 4, car.y + 10, 12, 18);
    ctx.fillRect(car.x + car.width / 2 - 16, car.y + 10, 12, 18);
  });
}

function drawOverlay() {
  if (state.running) return;

  ctx.fillStyle = "rgba(0,0,0,0.6)";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "#ffffff";
  ctx.font = "28px 'Segoe UI'";
  ctx.textAlign = "center";
  ctx.fillText("Crash!", canvas.width / 2, canvas.height / 2 - 10);

  ctx.font = "16px 'Segoe UI'";
  ctx.fillText("Hit restart to race again", canvas.width / 2, canvas.height / 2 + 20);
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawRoad();
  drawTraffic();
  drawPlayer();
  drawOverlay();
}

let lastTime = 0;
function loop(timestamp) {
  const delta = timestamp - lastTime || 16;
  lastTime = timestamp;

  update(delta);
  draw();

  requestAnimationFrame(loop);
}

restartBtn.addEventListener("click", () => {
  resetGame();
  bestEl.textContent = state.best;
});

window.addEventListener("keydown", (event) => {
  if (event.key === "ArrowLeft") keys.left = true;
  if (event.key === "ArrowRight") keys.right = true;
  if (event.key === "ArrowUp") keys.boost = true;
});

window.addEventListener("keyup", (event) => {
  if (event.key === "ArrowUp") keys.boost = false;
});

bestEl.textContent = state.best;
resetGame();
requestAnimationFrame(loop);
