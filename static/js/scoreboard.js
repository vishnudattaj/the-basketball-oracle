document.addEventListener('DOMContentLoaded', function () {
    const slider = document.getElementById('scorecardsSlider');
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');
    const container = document.querySelector('.scorecards-container');
    const scorecards = document.querySelectorAll('.scorecard');
    const indicatorsContainer = document.getElementById('carouselIndicators');

    // Convert rem to px
    function remToPx(rem) {
        const rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize);
        return rem * rootFontSize;
    }

    // Dynamically calculate how many cards fit based on container width
    function calculateVisibleCards() {
        const screenWidth = window.innerWidth;
        const targetCardWidth = 384;
        return Math.max(1, Math.floor(screenWidth / targetCardWidth));
    }




    let visibleCards = calculateVisibleCards();
    document.documentElement.style.setProperty('--visible-cards', visibleCards);
    const totalCards = scorecards.length;

    if (totalCards <= visibleCards) {
        prevButton.style.display = 'none';
        nextButton.style.display = 'none';
        return;
    }

    const totalPages = Math.ceil(totalCards / visibleCards);
    let currentPage = 0;

    function updateCardWidth() {
        const containerWidth = container.clientWidth;
        const gapRem = 0.75; // 12px
        const gapPx = remToPx(gapRem);

        const cardWidthPx = (containerWidth / visibleCards) - gapPx;
        const cardWidthRem = cardWidthPx / 16;

        scorecards.forEach(card => {
            card.style.minWidth = `${cardWidthRem}rem`;
            card.style.maxWidth = `${cardWidthRem}rem`;
        });

        return cardWidthRem;
    }




    let cardWidth = updateCardWidth();

    function goToPage(page) {
        page = Math.max(0, Math.min(page, totalPages - 1));
        currentPage = page;

        const positionRem = page * (visibleCards * (cardWidth + 0.9375)); // 15px → 0.9375rem
        slider.style.transform = `translateX(-${positionRem}rem)`;

        updateButtonStates();
    }

    function updateButtonStates() {
        prevButton.classList.toggle('disabled', currentPage <= 0);
        nextButton.classList.toggle('disabled', currentPage >= totalPages - 1);
    }

    updateButtonStates();

    prevButton.addEventListener('click', function () {
        if (currentPage > 0) {
            goToPage(currentPage - 1);
        }
    });

    nextButton.addEventListener('click', function () {
        if (currentPage < totalPages - 1) {
            goToPage(currentPage + 1);
        }
    });

    window.addEventListener('resize', function () {
        visibleCards = calculateVisibleCards();
        cardWidth = updateCardWidth();
        goToPage(currentPage);
    });


});

window.addEventListener('DOMContentLoaded', () => {
    const pixelRatio = window.devicePixelRatio;
    const tables = document.querySelectorAll('.standingsTable');

    tables.forEach((table) => {
        if (pixelRatio === 1) {
            table.classList.add('table-vh-1');
        } else if (pixelRatio === 1.25) {
            table.classList.add('table-vh-1_25');
        }
    });
});

window.addEventListener('DOMContentLoaded', () => {
    const pixelRatio = window.devicePixelRatio;
    const tables = document.querySelectorAll('.playerTable');

    tables.forEach((table) => {
        if (pixelRatio === 1) {
            table.classList.add('table-vh-1');
        } else if (pixelRatio === 1.25) {
            table.classList.add('table-vh-1_25');
        }
    });
});

window.addEventListener('DOMContentLoaded', () => {
    const pixelRatio = window.devicePixelRatio;
    const boxscoreTables = document.querySelectorAll('.boxscore');

    boxscoreTables.forEach((table) => {
        if (pixelRatio >= 1.24 && pixelRatio <= 1.26) {
            table.classList.remove('boxscore');
            table.classList.add('boxscore-scaled');
        }
    });
});
