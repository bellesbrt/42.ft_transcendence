
function renderRankingPage(sortedBy) {
	
	fetchAPI('/api/isAuthenticated').then(data => {
		
		if (data.isAuthenticated) {
			
			const validValues = ['solo', 'death', 'tournament', 'total', 'game', 'average', 'solo_inversed', 'death_inversed', 'tournament_inversed', 'total_inversed', 'game_inversed', 'average_inversed'];
			if (!validValues.includes(sortedBy)) {
				router.navigate('/ranking/total');
				return;
			}

			fetchAPI('/api/get_ranking_points/' + sortedBy).then(data => {
				
				if (data.success) {
					fetchAPI('/api/get_user').then(ndata => {
						
						if (ndata.user) {

							const users = data.users;
							split = sortedBy.includes('_');

							let html = `
								<div class="ranking-title">
									<h1>Ranking</h1>
									<button class="ranking-title-info">
										<img class="ranking-title-info-img" src="/static/chat/img/info.png" alt="Info">
									</button>
								</div>

								<table class="ranking-table" id="ranking-table">
									<tr>
										<th>User</th>
										<th>Total Points</th>
										<th>Games played</th>
										<th>Average Points</th>
									</tr>
							`;

							for (const user of Object.values(users)) {
								if (user.username == ndata.user.username) {
									html += `
										<tr class="rank-user">
									`;
								} else {
									html += `
										<tr>
									`;
								}

								html += `
										<td>
											<button class="rank-user-info" data-route="/profile/${user.username}">
												<img class="rank-image" src="${user.photo_url}" alt="photo">
												${safeText(user.username)}
											</button>
										</td>
										<td>${user.player.totalPoints[user.player.totalPoints.length - 1]}</td>
										<td>${user.player.totalPoints.length - 1}</td>
										<td>${user.player.averagePoints}</td>
									</tr>
								`;
							}

							html += `
								</table>
							`;

							document.getElementById('app').innerHTML = html;

							document.querySelector('.ranking-title-info').addEventListener('click', () => {
								let popupBackgroundHTML = '<div class="popup-background" id="popup-background"></div>';

								let popupHTML = `
									<div class="popup">
										<h3 class="title-popup">Ranking system</h3>
										<p class="popup-info-title">Solo games:</p>
										<p class="popup-info">The points won after a game represent the number of points scored during that game.</p>
								
										<p class="popup-info-title">DeathMatch games:</p>
										<p class="popup-info">
											10 points for the winner.</br>
											7 points for the second.</br>
											3 points for the third.</br>
											0 point for the last one.
										</p>

										<p class="popup-info-title">Tournament games:</p>
										<p class="popup-info">
											20 points for the winner.</br>
											15 points for the second.</br>
											7 points for the third.</br>
											0 point for the last one.
										</p>
									</div>
								`;

								let popupBackground = document.createElement('div');
								popupBackground.innerHTML = popupBackgroundHTML;
								document.body.appendChild(popupBackground);

								let popup = document.createElement('div');
								popup.innerHTML = popupHTML;
								document.body.appendChild(popup);

								document.getElementById('popup-background').addEventListener('click', () => {
									popup.remove();
									popupBackground.remove();
								});
							});

						}});
				} else {
					router.navigate('/pong/');
				}
			});
		} else {
			router.navigate('/sign_in/');
		}
	});
}