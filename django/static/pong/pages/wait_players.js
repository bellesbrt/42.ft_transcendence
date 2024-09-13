async function renderWaitPlayers(gameMode) {
    try {
        const authData = await fetchAPI('/api/isAuthenticated');

        if (!authData.isAuthenticated) {
            router.navigate('/sign_in/');
            return;
        }

        await fetchGamePage(gameMode);

        const gameData = await fetchAPI('/api/get_game_info');

        if (!gameData.success) {
            router.navigate('/pong/');
            return;
        }

        await fetchAPI('/api/change_status/waiting-game').then(data => {
            if (data.user_id) {
                changeStatus(data.user_id, 'waiting-game');
            }
        });

        const { game_id: gameID, player_id: playerID } = gameData;

        let html = `
            <div class="all-screen">
                <div class="waiting-game-infos">
                    <h2 class="waiting-game-title">Waiting for players</h2>
                </div>
        `;

        if (!['init_tournament_game', 'init_tournament_game_third_place_game', 'init_tournament_game_final_game'].includes(gameMode)) {
            html += `<button id="quit" class="quit-button">Quit</button>`;
        }

        html += `</div>`;

        document.getElementById('app').innerHTML = html;

        const quitButton = document.getElementById('quit');
        if (quitButton) {
            quitButton.addEventListener('click', async () => {
                try {
                    const quitResponse = await fetchAPI('/api/quit_game');

                    if (quitResponse.success) {
                        if (quitResponse.message === 'send-quit') {
                            send_message(quitResponse.room_id, 0, 'Invitation canceled');
                        }
                        if (pongSocket) {
                            pongSocket.socket.close();
                            pongSocket = null;
                        }
                        router.navigate('/pong/');
                    }
                } catch (error) {
                    console.error('Error quitting game:', error);
                }
            });
        }

        let dots = 0;
        const titleElement = document.querySelector('.waiting-game-title');
        const intervalId = setInterval(() => {
            if (!titleElement) {
                clearInterval(intervalId);
                return;
            }
            titleElement.innerHTML = 'Waiting for players' + '.'.repeat(dots);
            dots = (dots + 1) % 4;
        }, 500);

        gameProcess(true, gameMode, gameID, playerID);
    } catch (error) {
        console.error('Error rendering wait players page:', error);
        router.navigate('/pong/');
    }
}

async function fetchGamePage(gameMode) {
    try {
        const response = await fetch(`/pong/wait_players/${gameMode}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ gameMode })
        });

        if (response.headers.get('content-type').includes('application/json')) {
            const responseData = await response.json();

            if (responseData.success) {
                if (responseData.redirect === '/pong/game/' || responseData.gameMode !== gameMode) {
                    router.navigate(`${responseData.redirect}${responseData.gameMode}`);
                }
            }
        }
    } catch (error) {
        console.error('Error fetching game page:', error);
    }
}