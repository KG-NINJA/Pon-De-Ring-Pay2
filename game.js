const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// Game variables
let lastTime = 0;
let stage = 1;
let score = 0;
let gameStartTime = 0;
let battleship = null;

const player = {
    x: canvas.width / 2,
    y: canvas.height / 2,
    width: 30,
    height: 30,
    color: 'green',
    speed: 5,
    dx: 0,
    dy: 0,
    health: 100
};

const keys = {
    ArrowUp: false,
    ArrowDown: false,
    ArrowLeft: false,
    ArrowRight: false,
    ' ': false // Space for shooting
};

const bullets = [];
const missiles = [];
const warehouses = [];
const turrets = [];
const enemyBullets = [];
const fighters = [];

// Game loop
function gameLoop(timestamp) {
    let deltaTime = timestamp - lastTime;
    lastTime = timestamp;

    update(deltaTime);
    draw();

    requestAnimationFrame(gameLoop);
}

// Update game objects
function update(deltaTime) {
    // Move bullets
    for (let i = bullets.length - 1; i >= 0; i--) {
        const bullet = bullets[i];
        bullet.y += bullet.dy * bullet.speed;

        // Check for collision with warehouses
        for (let j = warehouses.length - 1; j >= 0; j--) {
            const warehouse = warehouses[j];
            if (
                bullet.x < warehouse.x + warehouse.width &&
                bullet.x + bullet.width > warehouse.x &&
                bullet.y < warehouse.y + warehouse.height &&
                bullet.y + bullet.height > warehouse.y
            ) {
                bullets.splice(i, 1);
                warehouse.health -= 10;
                if (warehouse.health <= 0) {
                    warehouses.splice(j, 1);
                    score += 100 * stage;
                }
                break;
            }
        }

        if (bullet.y < 0) {
            bullets.splice(i, 1);
        }
    }

    // Move missiles
    for (let i = missiles.length - 1; i >= 0; i--) {
        const missile = missiles[i];
        missile.y += missile.dy * missile.speed;

        // Check for collision with warehouses
        for (let j = warehouses.length - 1; j >= 0; j--) {
            const warehouse = warehouses[j];
            if (
                missile.x < warehouse.x + warehouse.width &&
                missile.x + missile.width > warehouse.x &&
                missile.y < warehouse.y + warehouse.height &&
                missile.y + missile.height > warehouse.y
            ) {
                missiles.splice(i, 1);
                warehouse.health -= 50;
                if (warehouse.health <= 0) {
                    warehouses.splice(j, 1);
                    score += 100 * stage;
                }
                break;
            }
        }

        if (missile.y < 0) {
            missiles.splice(i, 1);
        }
    }

    // Update turrets
    const currentTime = performance.now();
    for (const turret of turrets) {
        if (currentTime - turret.lastShotTime > turret.shootInterval) {
            turret.lastShotTime = currentTime;
            const angle = Math.atan2(player.y - turret.y, player.x - turret.x);
            const enemyBullet = {
                x: turret.x + turret.width / 2,
                y: turret.y + turret.height / 2,
                width: 5,
                height: 5,
                color: 'red',
                speed: 3 + stage,
                dx: Math.cos(angle),
                dy: Math.sin(angle)
            };
            enemyBullets.push(enemyBullet);
        }
    }

    // Move enemy bullets
    for (let i = enemyBullets.length - 1; i >= 0; i--) {
        const enemyBullet = enemyBullets[i];
        enemyBullet.x += enemyBullet.dx * enemyBullet.speed;
        enemyBullet.y += enemyBullet.dy * enemyBullet.speed;

        // Check for collision with player
        if (
            enemyBullet.x < player.x + player.width &&
            enemyBullet.x + enemyBullet.width > player.x &&
            enemyBullet.y < player.y + player.height &&
            enemyBullet.y + enemyBullet.height > player.y
        ) {
            enemyBullets.splice(i, 1);
            player.health -= 10;
            if (player.health <= 0) {
                // Game over
                console.log("Game Over");
                document.location.reload();
            }
        }

        if (
            enemyBullet.x < 0 ||
            enemyBullet.x > canvas.width ||
            enemyBullet.y < 0 ||
            enemyBullet.y > canvas.height
        ) {
            enemyBullets.splice(i, 1);
        }
    }

    // Update fighters
    for (let i = fighters.length - 1; i >= 0; i--) {
        const fighter = fighters[i];

        // Move
        fighter.x += Math.cos(fighter.angle) * fighter.speed;
        fighter.y += Math.sin(fighter.angle) * fighter.speed;

        // Turn towards player
        const targetAngle = Math.atan2(player.y - fighter.y, player.x - fighter.x);
        let angleDiff = targetAngle - fighter.angle;
        while (angleDiff > Math.PI) angleDiff -= 2 * Math.PI;
        while (angleDiff < -Math.PI) angleDiff += 2 * Math.PI;

        if (Math.abs(angleDiff) > fighter.turnSpeed) {
            fighter.angle += Math.sign(angleDiff) * fighter.turnSpeed;
        } else {
            fighter.angle = targetAngle;
        }

        // Check for collision with player weapons
        for (let j = bullets.length - 1; j >= 0; j--) {
            const bullet = bullets[j];
            if (
                bullet.x < fighter.x + fighter.width &&
                bullet.x + bullet.width > fighter.x &&
                bullet.y < fighter.y + fighter.height &&
                bullet.y + bullet.height > fighter.y
            ) {
                bullets.splice(j, 1);
                fighter.health -= 10;
            }
        }
        for (let j = missiles.length - 1; j >= 0; j--) {
            const missile = missiles[j];
            if (
                missile.x < fighter.x + fighter.width &&
                missile.x + missile.width > fighter.x &&
                missile.y < fighter.y + fighter.height &&
                missile.y + missile.height > fighter.y
            ) {
                missiles.splice(j, 1);
                fighter.health -= 50;
            }
        }

        if (fighter.health <= 0) {
            fighters.splice(i, 1);
            score += 200 * stage;
        }

        // Remove if off-screen
        if (fighter.x < -fighter.width || fighter.x > canvas.width + fighter.width || fighter.y > canvas.height + fighter.height) {
            fighters.splice(i, 1);
        }
    }

    // Update battleship
    if (battleship) {
        battleship.y += battleship.speed;

        // Battleship turrets
        const currentTime = performance.now();
        for (const turret of battleship.turrets) {
            turret.y = battleship.y; // Keep turrets on the battleship
            if (currentTime - turret.lastShotTime > turret.shootInterval) {
                turret.lastShotTime = currentTime;
                const angle = Math.atan2(player.y - turret.y, player.x - turret.x);
                const enemyBullet = {
                    x: turret.x + turret.width / 2,
                    y: turret.y + turret.height / 2,
                    width: 7,
                    height: 7,
                    color: 'orange',
                    speed: 5,
                    dx: Math.cos(angle),
                    dy: Math.sin(angle)
                };
                enemyBullets.push(enemyBullet);
            }
        }

        // Check for collision with player weapons
        for (let j = bullets.length - 1; j >= 0; j--) {
            const bullet = bullets[j];
            if (
                bullet.x < battleship.x + battleship.width &&
                bullet.x + bullet.width > battleship.x &&
                bullet.y < battleship.y + battleship.height &&
                bullet.y + bullet.height > battleship.y
            ) {
                bullets.splice(j, 1);
                battleship.health -= 10;
            }
        }
        for (let j = missiles.length - 1; j >= 0; j--) {
            const missile = missiles[j];
            if (
                missile.x < battleship.x + battleship.width &&
                missile.x + missile.width > battleship.x &&
                missile.y < battleship.y + battleship.height &&
                missile.y + missile.height > battleship.y
            ) {
                missiles.splice(j, 1);
                battleship.health -= 50;
            }
        }

        if (battleship.health <= 0) {
            battleship = null;
            // score += 10000;
        }

        if (battleship && battleship.y > canvas.height + battleship.height) {
            battleship = null;
        }
    } else {
        if (performance.now() - gameStartTime > 300000) { // 5 minutes
            createBattleship();
        }
    }

    if (warehouses.length === 0) {
        stage++;
        createWarehouses();
    }

    player.dx = 0;
    player.dy = 0;

    if (keys.ArrowUp) {
        player.dy = -player.speed;
    }
    if (keys.ArrowDown) {
        player.dy = player.speed;
    }
    if (keys.ArrowLeft) {
        player.dx = -player.speed;
    }
    if (keys.ArrowRight) {
        player.dx = player.speed;
    }

    player.x += player.dx;
    player.y += player.dy;

    // Wall collision
    if (player.x < 0) {
        player.x = 0;
    }
    if (player.x + player.width > canvas.width) {
        player.x = canvas.width - player.width;
    }
    if (player.y < 0) {
        player.y = 0;
    }
    if (player.y + player.height > canvas.height) {
        player.y = canvas.height - player.height;
    }
}

// Draw game objects
function draw() {
    // Clear canvas
    ctx.fillStyle = 'black';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw player
    ctx.fillStyle = player.color;
    ctx.fillRect(player.x, player.y, player.width, player.height);

    // Draw bullets
    for (const bullet of bullets) {
        ctx.fillStyle = bullet.color;
        ctx.fillRect(bullet.x, bullet.y, bullet.width, bullet.height);
    }

    // Draw missiles
    for (const missile of missiles) {
        ctx.fillStyle = missile.color;
        ctx.fillRect(missile.x, missile.y, missile.width, missile.height);
    }

    // Draw warehouses
    for (const warehouse of warehouses) {
        ctx.fillStyle = warehouse.color;
        ctx.fillRect(warehouse.x, warehouse.y, warehouse.width, warehouse.height);
    }

    // Draw turrets
    for (const turret of turrets) {
        ctx.fillStyle = turret.color;
        ctx.fillRect(turret.x, turret.y, turret.width, turret.height);
    }

    // Draw enemy bullets
    for (const enemyBullet of enemyBullets) {
        ctx.fillStyle = enemyBullet.color;
        ctx.fillRect(enemyBullet.x, enemyBullet.y, enemyBullet.width, enemyBullet.height);
    }

    // Draw fighters
    for (const fighter of fighters) {
        ctx.save();
        ctx.translate(fighter.x, fighter.y);
        ctx.rotate(fighter.angle + Math.PI / 2);
        ctx.fillStyle = fighter.color;
        ctx.fillRect(-fighter.width / 2, -fighter.height / 2, fighter.width, fighter.height);
        ctx.restore();
    }

    // Draw battleship
    if (battleship) {
        ctx.fillStyle = battleship.color;
        ctx.fillRect(battleship.x, battleship.y, battleship.width, battleship.height);
        for (const turret of battleship.turrets) {
            ctx.fillStyle = turret.color;
            ctx.fillRect(turret.x, turret.y, turret.width, turret.height);
        }
    }
}

function createWarehouses() {
    warehouses.length = 0;
    turrets.length = 0;
    for (let i = 0; i < 5; i++) {
        const warehouse = {
            x: Math.random() * (canvas.width - 100) + 50,
            y: Math.random() * (canvas.height / 2 - 100) + 50,
            width: 50,
            height: 50,
            color: 'gray',
            health: 100 * stage
        };
        warehouses.push(warehouse);
        createTurrets(warehouse);
    }
}

function createTurrets(warehouse) {
    const turret = {
        x: warehouse.x + warehouse.width / 2 - 5,
        y: warehouse.y - 10,
        width: 10,
        height: 10,
        color: 'red',
        shootInterval: 2000 / stage,
        lastShotTime: 0
    };
    turrets.push(turret);
}

function createFighter() {
    const fighter = {
        x: Math.random() * canvas.width,
        y: 0,
        width: 20,
        height: 20,
        color: 'purple',
        speed: 7,
        turnSpeed: 0.05,
        angle: Math.PI / 2,
        health: 50 * stage
    };
    fighters.push(fighter);
}

function createBattleship() {
    battleship = {
        x: canvas.width / 2,
        y: -200,
        width: 150,
        height: 100,
        color: 'darkred',
        speed: 1,
        health: 5000,
        turrets: []
    };
    // Add turrets to battleship
    for (let i = 0; i < 4; i++) {
        const turret = {
            x: battleship.x - 60 + i * 40,
            y: battleship.y,
            width: 15,
            height: 15,
            color: 'red',
            shootInterval: 1000,
            lastShotTime: 0
        };
        battleship.turrets.push(turret);
    }
}

// Start the game loop
gameStartTime = performance.now();
createWarehouses();
setInterval(createFighter, 5000 / stage);
requestAnimationFrame(gameLoop);

// Keyboard event listeners
window.addEventListener('keydown', (e) => {
    if (e.key in keys) {
        keys[e.key] = true;
    }
    if (e.key === ' ') {
        shootVulcan();
    }
    if (e.key === 'm') {
        shootMissile();
    }
});

window.addEventListener('keyup', (e) => {
    if (e.key in keys) {
        keys[e.key] = false;
    }
});

function shootVulcan() {
    const bullet = {
        x: player.x + player.width / 2,
        y: player.y + player.height / 2,
        width: 5,
        height: 5,
        color: 'yellow',
        speed: 10,
        dx: 0,
        dy: -1
    };
    bullets.push(bullet);
}

function shootMissile() {
    const missile = {
        x: player.x + player.width / 2,
        y: player.y + player.height / 2,
        width: 10,
        height: 10,
        color: 'orange',
        speed: 7,
        dx: 0,
        dy: -1
    };
    missiles.push(missile);
}
