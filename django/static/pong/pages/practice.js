async function renderPracticePage() {
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
            <h1>Practice game</h1>
            <h3>Choose a game mode</h3>
            <div class="choose-buttons">
                <button class="practice-btn" id="init_local_game">
                    <p class="choose-btn-title">Local game</p>
                    <p class="choose-btn-text">
                        1v1 game between you and a friend on the same computer.
                    </p>
                </button>
                <button class="practice-btn" id="init_ai_game">
                    <p class="choose-btn-title">1 vs AI</p>
                    <p class="choose-btn-text">
                        1v1 game between you and an opponent controlled by artificial intelligence.
                    </p>
                </button>
            </div>
            <button class="choose-back-btn" data-route="/pong/">↩ Back to menu</button>
        `;

        document.getElementById('app').innerHTML = html;

        document.querySelectorAll('.practice-btn').forEach(button => {
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
                            router.navigate(`${responseData.redirect}${responseData.gameMode}`);
                        }
                    }
                } catch (error) {
                    console.error('Error starting game:', error);
                }
            });
        });
    } catch (error) {
        console.error('Error rendering practice page:', error);
        router.navigate('/sign_in/');
    }
}