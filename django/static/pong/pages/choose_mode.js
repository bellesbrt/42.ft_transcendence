function renderChooseModePage() {

	fetchAPI('/api/isAuthenticated').then(data => {

		if (!data.isAuthenticated) {
			router.navigate('/sign_in/');
			return ;
		}

		const modesPage = `
			<h1>Pong game</h1>
			<h3 id="set-status-online">Choose a mode</h3>
			
			<div class="choose-buttons">
				<button class="choose-btn" data-route="/pong/practice/">
					<p class="choose-btn-title">Practice Mode</p>
				</button>
				
				<button class="choose-btn" data-route="/pong/ranked/">
					<p class="choose-btn-title">Ranked Mode</p>
				</button>
			</div>
		`;
		
		fetchAPI('/api/get_user').then(dataUser => {
			if (!dataUser.isAuthenticated) {
				router.navigate('/sign_in/');
				return;
			}

			if (!dataUser.user.player.currentGameID) {
				document.getElementById('app').innerHTML = modesPage;
			
			} else {
				let html = `
					<h1>Pong game</h1>
					<h3 id="set-status-online">You are already in a game</h3>
					
					<div class="choose-buttons">
						<button class="choose-btn" data-route="/pong/wait_players/${dataUser.user.player.gameMode}">
							<p class="choose-btn-title">Continue</p>
						</button>
					`;
				
				if ((['init_wall_game', 'init_ai_game', 'init_local_game'].includes(dataUser.user.player.gameMode)) || dataUser.user.player.isReady == false) {
					if (!['init_tournament_game', 'init_tournament_game_third_game_place', 'init_tournament_game_final_game', 'init_tournament_game_sub_game'].includes(dataUser.user.player.gameMode)) {
						html += `
								<button class="choose-btn" id="quit-game">
									<p class="choose-btn-title">Quit</p>
								</button>
							</div>
						`;
					}
				}
				else {
					html += `</div>`;
				}
				document.getElementById('app').innerHTML = html;
			}
			
			if (document.getElementById('quit-game')) {
				document.getElementById('quit-game').addEventListener('click', () => {
					fetchAPI('/api/quit_game').then(data => {
						if (data.success) {
							if (data.message == 'send-quit') {
								send_message(data.room_id, 0, 'Invitation canceled');
							}
							pongSocket.socket.close();
							pongSocket = null;
							router.navigate('/pong/');
						}
					});
				});
			}
			SignInProcess(dataUser.user.id);
		});
	})
}