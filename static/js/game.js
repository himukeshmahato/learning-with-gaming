const container = document.getElementById('game-container');
const pdfId = container.dataset.pdfid;

let questions = [];
let currentIndex = 0;
let score = 0;
let lives = 3;
let gameOver = false;
let gamePaused = false;
let attemptLog = [];
let gameSpeedMultiplier = 1;


// Config for Phaser
const config = {
    type: Phaser.AUTO,
    scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH,
        width: 800,
        height: 1200 // More vertical for mobile-first feel
    },
    parent: 'game-container',
    backgroundColor: '#0b1a13',
    physics: {
        default: 'arcade',
        arcade: {
            debug: false
        }
    },
    scene: {
        preload: preload,
        create: create,
        update: update
    }
};

let game;
let player;
let cursors;
let fallingOptions = [];
let questionText;
let scoreText;
let livesText;
let feedbackText;
let pauseOverlay;
let optionKeys = ['A', 'B', 'C', 'D'];
let isLeftPressed = false;
let isRightPressed = false;

// Fetch questions first after user clicks Start
window.initPhaserGame = function() {
    // CAPTURE LOBBY SETTINGS
    lives = window.GAME_LIVES || 3;
    gameSpeedMultiplier = window.GAME_SPEED || 1;
    let limit = window.QUESTION_COUNT || 10;
    
    // Reset game state for fresh start
    score = 0;
    currentIndex = 0;
    gameOver = false;
    attemptLog = [];

    fetch(`/game/api/questions/${pdfId}/?limit=${limit}`)
        .then(response => response.json())
        .then(data => {
            questions = data.questions;
            if(questions.length > 0) {
                window.gameInstance = new Phaser.Game(config);
            } else {
                container.innerHTML = "<h3 style='color:red;'>No questions were generated!</h3>";
            }
        });
};

function preload() {
    // Generate dummy textures so we don't need external assets
    let graphics = this.add.graphics();
    
    // Player basket (emerald color)
    graphics.fillStyle(0x10b981, 1);
    graphics.fillRoundedRect(0, 0, 140, 30, 8);
    graphics.generateTexture('player_basket', 140, 30);
    graphics.clear();
    
    // Falling block (surface color)
    graphics.fillStyle(0x12291d, 1);
    graphics.lineStyle(2, 0x1f422e, 1);
    graphics.fillRoundedRect(0, 0, 200, 80, 10);
    graphics.strokeRoundedRect(0, 0, 200, 80, 10);
    graphics.generateTexture('option_block', 200, 80);
    graphics.destroy();
}

function create() {
    // Add Grid Lines
    let gridGraphics = this.add.graphics({ lineStyle: { width: 1, color: 0x1f422e, alpha: 0.5 } });
    for(let i=0; i<900; i+=50) gridGraphics.strokeLineShape(new Phaser.Geom.Line(i, 0, i, 850));
    for(let j=0; j<850; j+=50) gridGraphics.strokeLineShape(new Phaser.Geom.Line(0, j, 900, j));

    // Top UI Panels - Multi-layered for premium feel and no overlap
    this.add.rectangle(400, 40, 800, 80, 0x0b1a13).setOrigin(0.5).setAlpha(0.9); // Main top bar
    this.add.rectangle(400, 120, 800, 80, 0x12291d).setOrigin(0.5).setAlpha(0.85); // Question panel
    
    scoreText = this.add.text(20, 20, 'SCORE: 0', { fontSize: '22px', fill: '#10b981', fontFamily: 'Outfit', fontWeight: '800' });
    livesText = this.add.text(780, 20, 'LIVES: ' + lives, { fontSize: '22px', fill: '#fbbf24', fontFamily: 'Outfit', fontWeight: '800' }).setOrigin(1, 0);
    
    questionText = this.add.text(450, 120, 'Loading mission...', { 
        fontSize: '22px', 
        fill: '#f8fafc', 
        fontFamily: 'Outfit',
        align: 'center',
        wordWrap: { width: 820 }
    }).setOrigin(0.5);

    feedbackText = this.add.text(450, 500, '', {
        fontSize: '38px',
        fill: '#fff',
        fontFamily: 'Outfit',
        fontWeight: '900',
        stroke: '#000',
        strokeThickness: 8
    }).setOrigin(0.5).setAlpha(0);

    // Pause overlay text (hidden by default)
    pauseOverlay = this.add.text(400, 600, 'PAUSED', {
        fontSize: '64px',
        fill: '#fbbf24',
        fontFamily: 'Outfit',
        fontWeight: '900',
        stroke: '#000',
        strokeThickness: 10
    }).setOrigin(0.5).setAlpha(0).setDepth(100);

    // Player
    player = this.physics.add.sprite(450, 810, 'player_basket');
    player.setCollideWorldBounds(true);
    
    cursors = this.input.keyboard.createCursorKeys();

    // Keyboard pause toggle (Space or P)
    this.input.keyboard.on('keydown-SPACE', () => { if (!gameOver) togglePause(); });
    this.input.keyboard.on('keydown-P', () => { if (!gameOver) togglePause(); });

    // Mobile Controls Events
    const lBtn = document.getElementById('left-btn');
    const rBtn = document.getElementById('right-btn');
    const pauseBtn = document.getElementById('pause-btn');
    if (lBtn && rBtn) {
        const setLeft = (val) => { isLeftPressed = val; };
        const setRight = (val) => { isRightPressed = val; };

        lBtn.addEventListener('touchstart', (e) => { e.preventDefault(); setLeft(true); });
        lBtn.addEventListener('touchend', (e) => { e.preventDefault(); setLeft(false); });
        lBtn.addEventListener('mousedown', () => setLeft(true));
        lBtn.addEventListener('mouseup', () => setLeft(false));
        lBtn.addEventListener('mouseleave', () => setLeft(false));

        rBtn.addEventListener('touchstart', (e) => { e.preventDefault(); setRight(true); });
        rBtn.addEventListener('touchend', (e) => { e.preventDefault(); setRight(false); });
        rBtn.addEventListener('mousedown', () => setRight(true));
        rBtn.addEventListener('mouseup', () => setRight(false));
        rBtn.addEventListener('mouseleave', () => setRight(false));
    }

    // Pause button events
    if (pauseBtn) {
        pauseBtn.addEventListener('click', (e) => { e.preventDefault(); if (!gameOver) togglePause(); });
        pauseBtn.addEventListener('touchstart', (e) => { e.preventDefault(); if (!gameOver) togglePause(); });
    }

    // Bug Fix: Close profile dropdown when touching the game canvas
    this.input.on('pointerdown', () => {
        const dropdown = document.getElementById('profileDropdown');
        if (dropdown) dropdown.classList.remove('show');
    });

    // Start with first question
    loadNextQuestion(this);
}

function togglePause() {
    gamePaused = !gamePaused;
    const pauseBtn = document.getElementById('pause-btn');
    if (gamePaused) {
        if (pauseBtn) { pauseBtn.textContent = '▶️'; pauseBtn.classList.add('paused'); }
        if (pauseOverlay) pauseOverlay.setAlpha(0.8);
    } else {
        if (pauseBtn) { pauseBtn.textContent = '⏸️'; pauseBtn.classList.remove('paused'); }
        if (pauseOverlay) pauseOverlay.setAlpha(0);
    }
}

function update(time, delta) {
    if (gameOver || gamePaused) return;

    // Normalizing factor for 60fps (16.66ms per frame)
    const dt = delta / 16.666;

    // Movement (Keyboard + Mobile Buttons)
    if (cursors.left.isDown || isLeftPressed) {
        player.setVelocityX(-500 * dt);
    } else if (cursors.right.isDown || isRightPressed) {
        player.setVelocityX(500 * dt);
    } else {
        player.setVelocityX(0);
    }

    // Touch support
    if (this.input.activePointer.isDown) {
        if (this.input.activePointer.x < player.x) {
            player.setVelocityX(-500 * dt);
        } else {
            player.setVelocityX(500 * dt);
        }
    }

    // Move falling objects
    fallingOptions.forEach(op => {
        if (op.active) {
            // Apply current live speed
            op.y += op.speed * (window.GAME_SPEED || 1) * dt;
            op.textObj.y = op.y;
            
            // Collision Check AABB
            if (Phaser.Geom.Intersects.RectangleToRectangle(player.getBounds(), op.getBounds())) {
                handleCollision(op.optionKey, this);
            }
            
            // Missed option
            if (op.y > 900) {
                op.active = false;
                op.setVisible(false);
                op.textObj.setVisible(false);
            }
        }
    });

    // If all options missed and not game over
    let activeBlocks = fallingOptions.filter(o => o.active);
    if(activeBlocks.length === 0 && !gameOver && feedbackText.alpha === 0) {
        lives -= 1;
        livesText.setText('LIVES: ' + lives);
        showFeedback(this, "Missed! Correct was " + questions[currentIndex].correct_answer, 0xff0000);
        
        attemptLog.push({
            question: questions[currentIndex].question,
            selected: 'None',
            correct: questions[currentIndex].correct_answer,
            explanation: questions[currentIndex].explanation,
            status: 'Missed'
        });

        currentIndex++;
        setTimeout(() => loadNextQuestion(this), 1500);
    }
}

function loadNextQuestion(scene) {
    if (lives <= 0 || currentIndex >= questions.length) {
        endGame(scene);
        return;
    }

    let qData = questions[currentIndex];
    questionText.setText(`Q${currentIndex+1}: ${qData.question}`);
    
    // BACKGROUND RE-FETCH: If we are near the end of available questions but haven't reached the user's requested limit
    let requestedLimit = window.QUESTION_COUNT || 10;
    if (questions.length < requestedLimit && currentIndex >= questions.length - 2) {
        fetch(`/game/api/questions/${pdfId}/?limit=${requestedLimit}`)
            .then(res => res.json())
            .then(data => {
                data.questions.forEach(newQ => {
                    if (!questions.find(q => q.id === newQ.id)) {
                        questions.push(newQ);
                        console.log("DEBUG: New question found and added in background.");
                    }
                });
            });
    }
    
    // Cleanup previous options
    fallingOptions.forEach(op => {
        op.destroy();
        op.textObj.destroy();
    });
    fallingOptions = [];

    // Spawn 4 options
    let xPositions = [150, 350, 550, 750];
    Phaser.Utils.Array.Shuffle(xPositions);
    
    let optionsList = [
        {k: 'A', text: qData.options.A},
        {k: 'B', text: qData.options.B},
        {k: 'C', text: qData.options.C},
        {k: 'D', text: qData.options.D}
    ];

    optionsList.forEach((opt, idx) => {
        // Start falling from BELOW the question panel (top 200px to be safe)
        let block = scene.add.sprite(xPositions[idx], 220 + (Math.random() * 60), 'option_block');
        block.speed = (0.5 + Math.random() * 0.5); // Removed multiplier here, applied in update
        block.optionKey = opt.k;
        
        let txt = scene.add.text(xPositions[idx], block.y, `${opt.k}. ${opt.text}`, {
            fontSize: '16px',
            fill: '#f8fafc',
            fontFamily: 'Outfit',
            align: 'center',
            wordWrap: { width: 180 }
        }).setOrigin(0.5);

        block.textObj = txt;
        fallingOptions.push(block);
    });
}

function handleCollision(selectedKey, scene) {
    // Immediately disable all blocks from colliding again to prevent double triggers
    fallingOptions.forEach(op => { 
        op.active = false; 
        if (op.optionKey === selectedKey) {
            op.setTint(0xfbbf24); // Highlight the caught option
        } else {
            op.setVisible(false);
            op.textObj.setVisible(false);
        }
    });
    
    let qData = questions[currentIndex];
    
    // Normalize comparison to prevent issues with whitespace or case
    const normalizedSelected = String(selectedKey).trim().toUpperCase();
    const normalizedCorrect = String(qData.correct_answer).trim().toUpperCase();
    
    if (normalizedSelected === normalizedCorrect) {
        score += 10;
        scoreText.setText('SCORE: ' + score);
        showFeedback(scene, `Correct! ${normalizedSelected} was right`, 0x10b981);
    } else {
        lives -= 1;
        livesText.setText('LIVES: ' + lives);
        showFeedback(scene, `Wrong! You caught ${normalizedSelected}. Correct was ${normalizedCorrect}`, 0xff0000);
    }
    
    attemptLog.push({
        question: qData.question,
        selected: normalizedSelected,
        correct: normalizedCorrect,
        explanation: qData.explanation,
        status: normalizedSelected === normalizedCorrect ? 'Correct' : 'Wrong'
    });

    currentIndex++;
    setTimeout(() => {
        loadNextQuestion(scene);
    }, 2000); // 2 second pause for feedback
}

function showFeedback(scene, msg, color) {
    feedbackText.setText(msg);
    feedbackText.setColor(color === 0x10b981 ? '#10b981' : '#ef4444');
    scene.tweens.add({
        targets: feedbackText,
        alpha: 1,
        duration: 300,
        yoyo: true,
        hold: 1400
    });
}

function endGame(scene) {
    gameOver = true;
    questionText.setText("Game Over!");
    
    let correctCount = score / 10;
    
    fallingOptions.forEach(op => {
        if(op) {op.destroy(); op.textObj.destroy();}
    });

    // POST Score to backend
    fetch('/game/api/score/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            pdf_id: pdfId,
            score: score,
            total_questions: questions.length,
            correct_answers: correctCount,
            wrong_answers: questions.length - correctCount,
            accuracy: questions.length > 0 ? (correctCount / questions.length) * 100 : 0,
            attempt_log: attemptLog
        })
    }).then(response => response.json())
    .then(data => {
        if(data.status === 'success') {
            window.location.href = `/game/result/${data.attempt_id}/`;
        } else {
            alert("Error saving score!");
            window.location.href = '/quiz/upload/';
        }
    });
}
