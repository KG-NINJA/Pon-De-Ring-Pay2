document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');

    const keys = {};
    document.addEventListener('keydown', (e) => {
        keys[e.key] = true;
    });
    document.addEventListener('keyup', (e) => {
        keys[e.key] = false;
    });

    const player = {
        x: canvas.width / 2 - 10,
        y: canvas.height - 40,
        width: 20,
        height: 20,
        speed: 4
    };

    const bullets = [];
    const enemies = [];
    let lastEnemySpawn = 0;
    let lastShot = 0;
    let score = 0;

    function spawnEnemy() {
        const x = Math.random() * (canvas.width - 20);
        enemies.push({ x, y: -20, width: 20, height: 20, speed: 1 + Math.random() * 2 });
    }

    function shoot() {
        bullets.push({ x: player.x + player.width / 2 - 2.5, y: player.y, width: 5, height: 10, speed: 6 });
    }

    function update() {
        if (keys['ArrowLeft'] || keys['a']) player.x -= player.speed;
        if (keys['ArrowRight'] || keys['d']) player.x += player.speed;
        if (keys['ArrowUp'] || keys['w']) player.y -= player.speed;
        if (keys['ArrowDown'] || keys['s']) player.y += player.speed;

        player.x = Math.max(0, Math.min(canvas.width - player.width, player.x));
        player.y = Math.max(0, Math.min(canvas.height - player.height, player.y));

        if (keys[' '] && Date.now() - lastShot > 250) {
            shoot();
            lastShot = Date.now();
        }

        bullets.forEach((b, i) => {
            b.y -= b.speed;
            if (b.y + b.height < 0) bullets.splice(i, 1);
        });

        enemies.forEach((e, ei) => {
            e.y += e.speed;
            if (e.y > canvas.height) {
                enemies.splice(ei, 1);
            }
            bullets.forEach((b, bi) => {
                if (b.x < e.x + e.width && b.x + b.width > e.x && b.y < e.y + e.height && b.y + b.height > e.y) {
                    bullets.splice(bi, 1);
                    enemies.splice(ei, 1);
                    score++;
                }
            });
        });

        if (Date.now() - lastEnemySpawn > 1000) {
            spawnEnemy();
            lastEnemySpawn = Date.now();
        }
    }

    function draw() {
        ctx.fillStyle = '#000';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = '#0f0';
        ctx.fillRect(player.x, player.y, player.width, player.height);

        ctx.fillStyle = '#ff0';
        bullets.forEach(b => {
            ctx.fillRect(b.x, b.y, b.width, b.height);
        });

        ctx.fillStyle = '#f00';
        enemies.forEach(e => {
            ctx.fillRect(e.x, e.y, e.width, e.height);
        });

        ctx.fillStyle = '#fff';
        ctx.fillText('Score: ' + score, 10, 20);
    }

    function loop() {
        update();
        draw();
        requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);
});
