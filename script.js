document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');

    const keys = {};
    document.addEventListener('keydown', (e) => { keys[e.key] = true; });
    document.addEventListener('keyup', (e) => { keys[e.key] = false; });

    const world = { width: 3000, height: 3000 };
    const player = { x: world.width / 2, y: world.height / 2, w: 24, h: 24, speed: 4, angle: 0, hp: 5 };
    const camera = { x: 0, y: 0 };

    const bullets = [];     // vulcan rounds
    const missiles = [];    // missiles
    const enemies = [];     // fighters
    const enemyBullets = []; // aa guns and fighters bullets
    const warehouses = [];
    let battleship = null;

    let lastVulcan = 0;
    let lastMissile = 0;
    let lastFighter = 0;
    let score = 0;
    let stage = 1;
    const startTime = Date.now();

    function spawnWarehouses() {
        warehouses.length = 0;
        for (let i = 0; i < 5; i++) {
            warehouses.push({
                x: Math.random() * (world.width - 100) + 50,
                y: Math.random() * (world.height - 100) + 50,
                w: 40,
                h: 40,
                hp: 40 * stage
            });
        }
    }
    spawnWarehouses();

    function fireVulcan() {
        bullets.push({
            x: player.x + player.w / 2,
            y: player.y + player.h / 2,
            dx: Math.cos(player.angle) * 8,
            dy: Math.sin(player.angle) * 8,
            w: 4,
            h: 4,
            dmg: 1
        });
    }

    function fireMissile() {
        missiles.push({
            x: player.x + player.w / 2,
            y: player.y + player.h / 2,
            dx: Math.cos(player.angle) * 6,
            dy: Math.sin(player.angle) * 6,
            w: 6,
            h: 6,
            dmg: 5
        });
    }

    function spawnFighter() {
        const edge = Math.floor(Math.random() * 4);
        let x = 0, y = 0;
        if (edge === 0) { x = 0; y = Math.random() * world.height; }
        if (edge === 1) { x = world.width; y = Math.random() * world.height; }
        if (edge === 2) { x = Math.random() * world.width; y = 0; }
        if (edge === 3) { x = Math.random() * world.width; y = world.height; }
        enemies.push({ x, y, w: 24, h: 24, angle: 0, speed: 5, turn: 0.05, hp: 3 });
    }

    function spawnBattleship() {
        battleship = { x: world.width, y: world.height / 2 - 50, w: 100, h: 100, hp: 100 };
    }

    function updatePlayer() {
        let vx = 0, vy = 0;
        if (keys['ArrowLeft'] || keys['a']) vx -= 1;
        if (keys['ArrowRight'] || keys['d']) vx += 1;
        if (keys['ArrowUp'] || keys['w']) vy -= 1;
        if (keys['ArrowDown'] || keys['s']) vy += 1;
        if (vx || vy) {
            const len = Math.hypot(vx, vy);
            player.angle = Math.atan2(vy, vx);
            player.x += (vx / len) * player.speed;
            player.y += (vy / len) * player.speed;
        }
        player.x = Math.max(0, Math.min(world.width - player.w, player.x));
        player.y = Math.max(0, Math.min(world.height - player.h, player.y));
        camera.x = player.x - canvas.width / 2;
        camera.y = player.y - canvas.height / 2;
        camera.x = Math.max(0, Math.min(world.width - canvas.width, camera.x));
        camera.y = Math.max(0, Math.min(world.height - canvas.height, camera.y));
        if (keys[' '] && Date.now() - lastVulcan > 100) {
            fireVulcan();
            lastVulcan = Date.now();
        }
        if (keys['Shift'] && Date.now() - lastMissile > 500) {
            fireMissile();
            lastMissile = Date.now();
        }
    }

    function updateShots(arr) {
        for (let i = arr.length - 1; i >= 0; i--) {
            const b = arr[i];
            b.x += b.dx;
            b.y += b.dy;
            if (b.x < 0 || b.y < 0 || b.x > world.width || b.y > world.height) {
                arr.splice(i, 1);
            }
        }
    }

    function hit(obj, b) {
        return b.x < obj.x + obj.w && b.x + b.w > obj.x && b.y < obj.y + obj.h && b.y + b.h > obj.y;
    }

    function updateWarehouses(elapsed) {
        const aaRate = 2000 / stage;
        warehouses.forEach((w) => {
            if (elapsed % aaRate < 16) {
                // fire a simple bullet towards player
                const dx = player.x - w.x;
                const dy = player.y - w.y;
                const d = Math.hypot(dx, dy) || 1;
                enemyBullets.push({ x: w.x + w.w / 2, y: w.y + w.h / 2, dx: dx / d * 4, dy: dy / d * 4, w: 4, h: 4 });
            }
        });
    }

    function updateEnemies() {
        enemies.forEach((e) => {
            const dx = player.x - e.x;
            const dy = player.y - e.y;
            const desired = Math.atan2(dy, dx);
            let diff = desired - e.angle;
            diff = Math.atan2(Math.sin(diff), Math.cos(diff));
            e.angle += diff * e.turn;
            e.x += Math.cos(e.angle) * e.speed;
            e.y += Math.sin(e.angle) * e.speed;
        });
    }

    function updateBattleship() {
        if (!battleship) return;
        battleship.x -= 1;
        if (battleship.x + battleship.w < 0) battleship = null;
        if (Math.random() < 0.02) {
            const dx = player.x - battleship.x;
            const dy = player.y - battleship.y;
            const d = Math.hypot(dx, dy) || 1;
            enemyBullets.push({ x: battleship.x + battleship.w / 2, y: battleship.y + battleship.h / 2, dx: dx / d * 5, dy: dy / d * 5, w: 6, h: 6 });
        }
    }

    function collisions() {
        // player hit
        enemyBullets.forEach((b, i) => {
            if (hit(player, b)) {
                enemyBullets.splice(i, 1);
                player.hp -= 1;
            }
        });
        // bullets vs enemies
        bullets.forEach((b, bi) => {
            enemies.forEach((e, ei) => {
                if (hit(e, b)) {
                    bullets.splice(bi, 1);
                    e.hp -= b.dmg;
                }
            });
            warehouses.forEach((w, wi) => {
                if (hit(w, b)) {
                    bullets.splice(bi, 1);
                    w.hp -= b.dmg;
                }
            });
            if (battleship && hit(battleship, b)) {
                bullets.splice(bi, 1);
                battleship.hp -= b.dmg;
            }
        });
        missiles.forEach((m, mi) => {
            enemies.forEach((e, ei) => {
                if (hit(e, m)) {
                    missiles.splice(mi, 1);
                    e.hp -= m.dmg;
                }
            });
            warehouses.forEach((w, wi) => {
                if (hit(w, m)) {
                    missiles.splice(mi, 1);
                    w.hp -= m.dmg;
                }
            });
            if (battleship && hit(battleship, m)) {
                missiles.splice(mi, 1);
                battleship.hp -= m.dmg;
            }
        });
        enemies.forEach((e, ei) => { if (e.hp <= 0) { enemies.splice(ei, 1); score += 10; } });
        warehouses.forEach((w, wi) => { if (w.hp <= 0) { warehouses.splice(wi, 1); score += 50; } });
        if (battleship && battleship.hp <= 0) { battleship = null; score += 500; }
    }

    function checkStageClear() {
        if (warehouses.length === 0) {
            stage += 1;
            spawnWarehouses();
            player.hp = 5;
        }
    }

    function update() {
        const elapsed = Date.now() - startTime;
        updatePlayer();
        updateShots(bullets);
        updateShots(missiles);
        updateShots(enemyBullets);
        updateEnemies();
        updateWarehouses(elapsed);
        if (elapsed > 300000 && !battleship) spawnBattleship();
        updateBattleship();
        collisions();
        if (elapsed - lastFighter > 10000) { spawnFighter(); lastFighter = elapsed; }
        checkStageClear();
    }

    function draw() {
        ctx.fillStyle = '#000';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.save();
        ctx.translate(-camera.x, -camera.y);
        ctx.fillStyle = '#0f0';
        ctx.fillRect(player.x, player.y, player.w, player.h);
        ctx.fillStyle = '#ff0';
        bullets.forEach(b => ctx.fillRect(b.x, b.y, b.w, b.h));
        ctx.fillStyle = '#0ff';
        missiles.forEach(m => ctx.fillRect(m.x, m.y, m.w, m.h));
        ctx.fillStyle = '#f00';
        enemyBullets.forEach(b => ctx.fillRect(b.x, b.y, b.w, b.h));
        ctx.fillStyle = '#aaa';
        enemies.forEach(e => ctx.fillRect(e.x, e.y, e.w, e.h));
        ctx.fillStyle = '#555';
        warehouses.forEach(w => ctx.fillRect(w.x, w.y, w.w, w.h));
        if (battleship) {
            ctx.fillStyle = '#800';
            ctx.fillRect(battleship.x, battleship.y, battleship.w, battleship.h);
        }
        ctx.restore();
        ctx.fillStyle = '#fff';
        ctx.fillText('Score: ' + score, 10, 20);
        ctx.fillText('HP: ' + player.hp, 10, 40);
        ctx.fillText('Stage: ' + stage, 10, 60);
    }

    function loop() {
        update();
        draw();
        if (player.hp > 0) {
            requestAnimationFrame(loop);
        } else {
            ctx.fillStyle = '#fff';
            ctx.fillText('Game Over', canvas.width / 2 - 40, canvas.height / 2);
        }
    }
    requestAnimationFrame(loop);
});
