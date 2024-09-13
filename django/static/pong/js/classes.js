class Field {
	constructor(size) {
		this.x = sizes.field;
		this.y = sizes.field;
		this.width = size - sizes.field * 2;
		this.height = size - sizes.field * 2;
	}

	draw(context) {
		context.fillStyle = "#E0FFFF";
		context.fillRect(this.x, this.y, this.width, this.height);
	}
}

class Ball {
	constructor(x, y, color, radius) {
		this.x = x;
		this.y = y;
		this.color = color;
		this.radius = radius;
		this.context = this.initializeContext('ballLayer');
	}

	initializeContext(layerId) {
		const canvas = document.getElementById(layerId);
		if (canvas) {
			canvas.width = sizes.canvas;
			canvas.height = sizes.canvas;
			return canvas.getContext('2d');
		}
		return null;
	}

	draw(x = this.x, y = this.y, color = this.color, radius = this.radius) {
		if (this.context) {
			this.x = x;
			this.y = y;
			this.color = color;
			this.radius = radius;
			this.context.fillStyle = this.color;
			this.context.beginPath();
			this.context.arc(this.x, this.y, this.radius, 0, 2 * Math.PI);
			this.context.fill();
		}
	}

	clear() {
		if (this.context) {
			this.context.clearRect(0, 0, sizes.canvas, sizes.canvas);
		}
	}
}

class Paddle {
	constructor(paddleID) {
		this.id = paddleID;
		this.width = sizes.paddleThickness;
		this.height = sizes.paddleSize;
		if (paddleID >= 2) {
			[this.width, this.height] = [sizes.paddleSize, sizes.paddleThickness];
		}
		this.context = this.initializeContext('paddle' + (paddleID + 1) + 'Layer');
	}

	initializeContext(layerId) {
		const canvas = document.getElementById(layerId);
		if (canvas) {
			canvas.width = sizes.canvas;
			canvas.height = sizes.canvas;
			return canvas.getContext('2d');
		}
		return null;
	}

	draw(position) {
		if (this.context) {
			const bottomLimit = sizes.offset;
			const topLimit = sizes.canvas - sizes.field;
			const paddleXpos = [bottomLimit, topLimit, position, position];
			const paddleYpos = [position, position, bottomLimit, topLimit];
			const paddleColors = ['#E21E59', '#1598E9', '#2FD661', '#F19705'];

			this.x = paddleXpos[this.id];
			this.y = paddleYpos[this.id];
			this.color = paddleColors[this.id];

			this.context.fillStyle = this.color;
			this.context.fillRect(this.x, this.y, this.width, this.height);
		}
	}

	clear() {
		if (this.context) {
			this.context.clearRect(0, 0, sizes.canvas, sizes.canvas);
		}
	}
}