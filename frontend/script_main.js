// ===== DRAGGABLE MENU FUNCTIONALITY =====

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

// ===== TOGGLE MENU EXPANSION =====
menuToggler.addEventListener('click', (e) => {
    e.stopPropagation();
    menuDrawer.classList.toggle('expanded');
    menuToggler.classList.toggle('active');
});

// ===== SMOOTH DRAG FUNCTIONALITY WITH RAF =====
menuDrawer.addEventListener('mousedown', dragStart, { passive: false });
document.addEventListener('mousemove', drag, { passive: false });
document.addEventListener('mouseup', dragEnd);

// Touch events for mobile
menuDrawer.addEventListener('touchstart', dragStart, { passive: false });
document.addEventListener('touchmove', drag, { passive: false });
document.addEventListener('touchend', dragEnd);

function dragStart(e) {
    // Don't drag if clicking on toggler or menu items
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
    menuDrawer.style.transition = 'none'; // Remove transitions during drag
}

function drag(e) {
    if (!isDragging) return;

    e.preventDefault();

    // Update current position immediately
    if (e.type === 'touchmove') {
        currentX = e.touches[0].clientX - initialX;
        currentY = e.touches[0].clientY - initialY;
    } else {
        currentX = e.clientX - initialX;
        currentY = e.clientY - initialY;
    }

    // Use requestAnimationFrame for smooth 60fps updates
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

    // Re-enable transitions
    menuDrawer.style.transition = '';

    // Keep within viewport bounds with smooth animation
    constrainToViewport();
}

function setTranslate(xPos, yPos, el) {
    // Use translate3d for hardware acceleration
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

    // Check horizontal bounds
    if (rect.left < 0) {
        newX = xOffset - rect.left;
        needsConstrain = true;
    } else if (rect.right > viewportWidth) {
        newX = xOffset - (rect.right - viewportWidth);
        needsConstrain = true;
    }

    // Check vertical bounds
    if (rect.top < 0) {
        newY = yOffset - rect.top;
        needsConstrain = true;
    } else if (rect.bottom > viewportHeight) {
        newY = yOffset - (rect.bottom - viewportHeight);
        needsConstrain = true;
    }

    // Apply constrained position with smooth transition
    if (needsConstrain) {
        xOffset = newX;
        yOffset = newY;
        menuDrawer.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        setTranslate(newX, newY, menuDrawer);

        // Remove transition after animation
        setTimeout(() => {
            menuDrawer.style.transition = '';
        }, 300);
    }
}

// ===== CLOSE MENU WHEN CLICKING OUTSIDE =====
document.addEventListener('click', (e) => {
    if (!menuDrawer.contains(e.target) && menuDrawer.classList.contains('expanded')) {
        menuDrawer.classList.remove('expanded');
        menuToggler.classList.remove('active');
    }
});

// ===== SMOOTH MENU ITEM CLICKS =====
document.querySelectorAll('.menu-item a').forEach(link => {
    link.addEventListener('click', (e) => {
        // Add click feedback
        e.currentTarget.parentElement.style.transform = 'scale(0.95)';
        setTimeout(() => {
            e.currentTarget.parentElement.style.transform = '';
        }, 150);
    });
});

// ===== WINDOW RESIZE HANDLER =====
window.addEventListener('resize', constrainToViewport);
