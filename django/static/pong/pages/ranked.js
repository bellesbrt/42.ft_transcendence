async function renderRankedPage() {
    try {
        const authData = await fetchAPI('/api/isAuthenticated');

        if (!authData.isAuthenticated) {
            router.navigate('/sign_in/');
            return;
        }

        const userData = await fetchAPI('/api/get_user');

        if (userData.user.player.currentGameID) {
            router.navigate('/pong/');
            return;
        }

        const html = `
            <h1>Ranked game</h1>
            <h3>Choose a game mode</h3>
            <div class="choose-buttons">
                <button class="ranked-btn" id="init_ranked_solo_game">
                    <p class="choose-btn-title">1 vs 1</p>
                    <p class="choose-btn-text">
                        Solo play against a random opponent from around the world.
                    </p>
                </button>
                <button class="ranked-btn" id="init_death_game">
                    <p class="choose-btn-title">Deathmatch Game</p>
                    <p class="choose-btn-text">
                        4 players play on the same board. The last one standing wins the game.
                    </p>
                </button>
                <button class="ranked-btn" id="init_tournament_game">
                    <p class="choose-btn-title">Tournament</p>
                    <p class="choose-btn-text">
                        4 players play on 2 boards in 1v1. The 2 winners play against each other.
                        The last one standing wins the tournament.
                    </p>
                </button>
            </div>
            <button class="choose-back-btn" data-route="/pong/">↩ Back to menu</button>
        `;

        document.getElementById('app').innerHTML = html;

        document.querySelectorAll('.ranked-btn').forEach(button => {
            button.addEventListener('click', async event => {
                const gameMode = event.currentTarget.id;

                try {
                    const response = await fetch(`/pong/wait_players/${gameMode}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken'),
                        },
                        body: JSON.stringify({ gameMode }),
                    });

                    if (response.ok) {
                        const responseData = await response.json();

                        if (responseData.success) {
                            if (gameMode === 'init_tournament_game') {
                                const tournamentData = await fetchAPI('/api/join_tournament');
                                if (tournamentData.room_id) {
                                    send_tournament_message(tournamentData.room_id);
                                }
                            }
                            router.navigate(`${responseData.redirect}${responseData.gameMode}`);
                        }
                    }
                } catch (error) {
                    console.error('Error starting ranked game:', error);
                }
            });
        });
    } catch (error) {
        console.error('Error rendering ranked page:', error);
        router.navigate('/sign_in/');
    }
}

function send_tournament_message(room_id) {
    const websocketProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const websocketPort = window.location.protocol === 'https:' ? ':8443' : ':8000';
    const socketUrl = `${websocketProtocol}//${window.location.hostname}${websocketPort}/ws/chat/${room_id}/`;

    const tmpSocket = new WebSocket(socketUrl);

    tmpSocket.onopen = () => {
        tmpSocket.send(JSON.stringify({
            message: "Tournament game is starting! Players get ready!",
            sender: 0,
            username: 'System Info',
        }));
    };

    tmpSocket.onclose = () => {
        tmpSocket.shouldClose = true;
    };
}