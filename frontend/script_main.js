
const menuDrawer = document.getElementById('menuDrawer');
const menuToggler = document.getElementById('menuToggler');
let isDragging = false;
let currentX = 0;
let currentY = 0;
let initialX = 0;
let initialY = 0;
let xOffset = 0;
let yOffset = 0;
let animationFrameId = null;

menuToggler.addEventListener('click', (e) => {
    e.stopPropagation();
    menuDrawer.classList.toggle('expanded');
    menuToggler.classList.toggle('active');
});

menuDrawer.addEventListener('mousedown', dragStart, { passive: false });
document.addEventListener('mousemove', drag, { passive: false });
document.addEventListener('mouseup', dragEnd);

menuDrawer.addEventListener('touchstart', dragStart, { passive: false });
document.addEventListener('touchmove', drag, { passive: false });
document.addEventListener('touchend', dragEnd);

function dragStart(e) {
    if (e.target.closest('.menu-toggler') || e.target.closest('.menu-item')) {
        return;
    }

    if (e.type === 'touchstart') {
        initialX = e.touches[0].clientX - xOffset;
        initialY = e.touches[0].clientY - yOffset;
    } else {
        initialX = e.clientX - xOffset;
        initialY = e.clientY - yOffset;
    }

    isDragging = true;
    menuDrawer.classList.add('dragging');
    menuDrawer.style.transition = 'none';
}

function drag(e) {
    if (!isDragging) return;

    e.preventDefault();

    if (e.type === 'touchmove') {
        currentX = e.touches[0].clientX - initialX;
        currentY = e.touches[0].clientY - initialY;
    } else {
        currentX = e.clientX - initialX;
        currentY = e.clientY - initialY;
    }

    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
    }

    animationFrameId = requestAnimationFrame(() => {
        xOffset = currentX;
        yOffset = currentY;
        setTranslate(currentX, currentY, menuDrawer);
    });
}

function dragEnd(e) {
    if (!isDragging) return;

    initialX = currentX;
    initialY = currentY;
    isDragging = false;
    menuDrawer.classList.remove('dragging');

    menuDrawer.style.transition = '';

    constrainToViewport();
}

function setTranslate(xPos, yPos, el) {
    el.style.transform = `translate3d(${xPos}px, ${yPos}px, 0)`;
    el.style.willChange = 'transform';
}

function constrainToViewport() {
    const rect = menuDrawer.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let newX = xOffset;
    let newY = yOffset;
    let needsConstrain = false;

    if (rect.left < 0) {
        newX = xOffset - rect.left;
        needsConstrain = true;
    } else if (rect.right > viewportWidth) {
        newX = xOffset - (rect.right - viewportWidth);
        needsConstrain = true;
    }

    if (rect.top < 0) {
        newY = yOffset - rect.top;
        needsConstrain = true;
    } else if (rect.bottom > viewportHeight) {
        newY = yOffset - (rect.bottom - viewportHeight);
        needsConstrain = true;
    }

    if (needsConstrain) {
        xOffset = newX;
        yOffset = newY;
        menuDrawer.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        setTranslate(newX, newY, menuDrawer);

        setTimeout(() => {
            menuDrawer.style.transition = '';
        }, 300);
    }
}

document.addEventListener('click', (e) => {
    if (!menuDrawer.contains(e.target) && menuDrawer.classList.contains('expanded')) {
        menuDrawer.classList.remove('expanded');
        menuToggler.classList.remove('active');
    }
});

document.querySelectorAll('.menu-item a').forEach(link => {
    link.addEventListener('click', (e) => {
        e.currentTarget.parentElement.style.transform = 'scale(0.95)';
        setTimeout(() => {
            e.currentTarget.parentElement.style.transform = '';
        }, 150);
    });
});

window.addEventListener('resize', constrainToViewport);
