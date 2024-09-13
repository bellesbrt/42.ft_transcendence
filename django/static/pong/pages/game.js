async function renderGamePage(gameMode) {
    try {
        const authData = await fetchAPI('/api/isAuthenticated');
        
        if (!authData.isAuthenticated) {
            router.navigate('/sign_in/');
            return;
        }

        const gameInfo = await fetchAPI('/api/get_game_info');
        
        if (!gameInfo.success) {
            router.navigate('/pong/');
            return;
        }

        const statusData = await fetchAPI('/api/change_status/in-game');
        if (statusData.user_id) {
            changeStatus(statusData.user_id, statusData.status);
        }

        const { game_id, player_id, players_username, players_photo, room_id, type_game } = gameInfo;
        let html = `
            <h1>Pong game</h1>
            <div class="game-participant-list">
        `;

        const positions = ["left", "right", "top", "bottom"];
        if (players_username.length > 1) {
            players_username.forEach((username, i) => {
                html += `
                <div class="game-participant">
                    <img class="game-participants-img" src="${players_photo[i]}" alt="photo">
                    <h3 class="game-participants-name ${positions[i]}">${safeText(username)}</h3>
                </div>
                `;
            });
        }

        html += `
            </div>
            <div class="score_bar">
                <span class="player_score id0"></span>
                <span class="player_score id1"></span>
                <span class="player_score id2"></span>
                <span class="player_score id3"></span>
            </div>
            <canvas id="gameCanvas"></canvas>
            <canvas id="ballLayer"></canvas>
            <canvas id="paddle1Layer"></canvas>
            <canvas id="paddle2Layer"></canvas>
            <canvas id="paddle3Layer"></canvas>
            <canvas id="paddle4Layer"></canvas>
            <div class="fill_pong_space"></div>
        `;

        if (type_game === "local") {
            html += `
            <div class="game-buttons">
                <button class="choose-back-btn game-button" id="quit">↩ Quit game</button>
            </div>
            `;
        }

        document.getElementById('app').innerHTML = html;
        gameProcess(false, gameMode, game_id, player_id);

        const quitButton = document.getElementById('quit');
        if (quitButton) {
            quitButton.addEventListener('click', async () => {
                const quitResponse = await fetchAPI('/api/quit_game');
                if (quitResponse.success) {
                    if (pongSocket) {
                        pongSocket.socket.close();
                        pongSocket = null;
                    }
                    router.navigate('/pong/');
                }
            });
        }
    } catch (error) {
        console.error('Error rendering game page:', error);
        router.navigate('/pong/');
    }
}