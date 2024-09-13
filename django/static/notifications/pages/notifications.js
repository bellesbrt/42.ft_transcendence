let totalMessages = {};

function renderNotification(notification, index) {
    const { id, redirect, title, message, date, type, userID } = notification;
    const isFriendRequest = type === 'request-friend';
    return `
        <div data-ignore-click data-route="${redirect}" data-notification-id="${id}" class="notification" data-index="${index}">
            <div class="notification-containers">
                <div class="notification-content">
                    <span class="notification-title" data-index="${index}">${safeText(title)}</span>
                    <span class="notification-message" data-index="${index}">${safeText(message)}</span>
                    <span class="notification-date" data-index="${index}">${safeText(date)}</span>
                    <div class="notification-buttons">
                        ${isFriendRequest ? `
                        <a data-ignore-click data-notification-id="${id}" data-user-id="${userID}">
                            <p class="notification-button-text">Accept</p>
                        </a>
                        ` : ''}
                        <a data-ignore-click class="notification-delete" data-notification-id="${id}">
                            <img class="notification-delete-img" src="/static/notifications/img/delete.png" alt="Delete">
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function updateNotificationStyles(index, notification) {
    if (!notification.read) {
        const notificationElement = document.querySelector(`.notification[data-index="${index}"]`);
        notificationElement.style.backgroundColor = '#F3F2ED';
        notificationElement.querySelector('.notification-title').style.color = 'black';
        const message = notificationElement.querySelector('.notification-message');
        message.style.fontWeight = 'bold';
        message.style.color = 'black';
        const date = notificationElement.querySelector('.notification-date');
        date.style.fontWeight = 'bold';
        date.style.color = 'black';
    }
}

function countAndRenderMessages(reversedNotifications) {
    reversedNotifications.forEach((notification, index) => {
        if (notification.type === 'message') {
            const channel = notification.message;
            if (!totalMessages[channel]) {
                totalMessages[channel] = [notification];
                reversedNotifications.forEach((noti) => {
                    if (noti !== totalMessages[channel][0] && noti.type === 'message' && noti.message === channel) {
                        totalMessages[channel].push(noti);
                    }
                });

                totalMessages[channel][0].message = totalMessages[channel].length === 1
                    ? `You have a new message from ${totalMessages[channel][0].message}`
                    : `You have ${totalMessages[channel].length} new messages from ${totalMessages[channel][0].message}`;

                document.getElementById('app').innerHTML += renderNotification(totalMessages[channel][0], index);
                updateNotificationStyles(index, totalMessages[channel][0]);
            }
        } else {
            document.getElementById('app').innerHTML += renderNotification(notification, index);
            updateNotificationStyles(index, notification);
        }
    });
}

function renderNotificationsPage() {
    fetchAPI('/api/isAuthenticated').then(data => {
        if (!data.isAuthenticated) {
            router.navigate('/sign_in/');
            return;
        }
    });

    fetchAPI('/api/get_notifications').then(data => {
        renderHeader();
        const reversedNotifications = Object.values(data.notifications).reverse();
        document.getElementById('app').innerHTML = `
            <h1>Notifications</h1>
            <div class="notifications-actions">
                <div class="notifications-filters">
                    <p class="notification-filter-title">Filters:</p>
                    <a data-ignore-click class="notification-filter" data-filter="all">All</a>
                    <p class="notification-filter-divider">|</p>
                    <a data-ignore-click class="notification-filter" data-filter="messages">Messages</a>
                    <p class="notification-filter-divider">|</p>
                    <a data-ignore-click class="notification-filter" data-filter="requests">Friends requests</a>
                </div>
                <a class="notification-delete-all">Delete All</a>
            </div>
        `;

        if (reversedNotifications.length === 0) {
            document.getElementById('app').innerHTML += `<p class="no-notification">No notifications.</p>`;
        } else {
            totalMessages = {};
            countAndRenderMessages(reversedNotifications);
        }

        addEventListeners();
        document.querySelector('.notification-filter[data-filter="all"]').style.border = '1px solid #474747';
    });
}

function addEventListeners() {
    document.querySelectorAll('.notification-delete').forEach(button => {
        button.addEventListener('click', async (event) => {
            event.preventDefault();
            const notificationId = button.getAttribute('data-notification-id');
            if (!notificationId) return;

            const deletePromises = totalMessages.flatMap(messageList =>
                messageList[0].id === parseInt(notificationId)
                    ? messageList.map(notification => fetchAPI(`/api/delete_notification/${notification.id}`))
                    : []
            );

            if (deletePromises.length === 0) {
                deletePromises.push(fetchAPI(`/api/delete_notification/${notificationId}`));
            }

            await Promise.all(deletePromises);
            router.navigate('/notifications/');
        });
    });

    document.querySelector('.notification-delete-all').addEventListener('click', async (event) => {
        event.preventDefault();
        await fetchAPI('/api/delete_all_notifications');
        router.navigate('/notifications/');
    });

    document.querySelectorAll('.notification').forEach(notification => {
        notification.addEventListener('click', (event) => {
            if (event.target.classList.contains('notification-delete') || event.target.classList.contains('notification-button-text')) return;
            event.preventDefault();
            const notificationId = notification.getAttribute('data-notification-id');
            fetchAPI(`/api/interacted_notification/${notificationId}`).then(() => {
                const url = notification.getAttribute('data-route');
                router.navigate(url);
            });
        });
    });

    document.querySelectorAll('.notification-buttons a').forEach(button => {
        button.addEventListener('click', async (event) => {
            event.preventDefault();
            const notificationId = button.getAttribute('data-notification-id');
            const userID = button.getAttribute('data-user-id');
            if (!notificationId || !userID) return;

            await fetchAPI(`/api/follow/${userID}`);
            await fetchAPI(`/api/delete_notification/${notificationId}`);
            router.navigate('/notifications/');
        });
    });

    document.querySelectorAll('.notification-filter').forEach(filter => {
        filter.addEventListener('click', (event) => {
            event.preventDefault();
            const filterName = filter.getAttribute('data-filter');
            if (!filterName) return;

            document.querySelectorAll('.notification-filter').forEach(f => f.style.border = '0px solid #474747');

            document.querySelectorAll('.notification').forEach(notification => {
                const title = notification.querySelector('.notification-title').textContent;
                notification.style.display = filterName === 'all' ? 'flex' :
                    filterName === 'messages' && title.includes('New message') ? 'flex' :
                    filterName === 'requests' && title.includes('New friend request') ? 'flex' : 'none';
            });

            filter.style.border = '1px solid #474747';
        });
    });
}
