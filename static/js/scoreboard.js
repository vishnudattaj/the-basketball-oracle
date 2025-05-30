document.addEventListener('DOMContentLoaded', function() {
    const slider = document.getElementById('scorecardsSlider');
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');
    const container = document.querySelector('.scorecards-container');
    const scorecards = document.querySelectorAll('.scorecard');
    const indicatorsContainer = document.getElementById('carouselIndicators');
    let visibleCards;

    if (window.devicePixelRatio >= 1.24 && window.devicePixelRatio <= 1.26) {
        visibleCards = 4;
    } else {
        visibleCards = 5;
    }

    console.log("Visible Cards:", visibleCards);
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
        const cardWidth = (containerWidth / visibleCards) - 12;

        scorecards.forEach(card => {
            card.style.minWidth = `${cardWidth}px`;
            card.style.maxWidth = `${cardWidth}px`;
        });

        return cardWidth;
    }

    let cardWidth = updateCardWidth();

    function goToPage(page) {
        page = Math.max(0, Math.min(page, totalPages - 1));

        currentPage = page;

        const position = page * (visibleCards * (cardWidth + 15));

        slider.style.transform = `translateX(-${position}px)`;

        updateButtonStates();
    }

    function updateButtonStates() {
        prevButton.classList.toggle('disabled', currentPage <= 0);
        nextButton.classList.toggle('disabled', currentPage >= totalPages - 1);
    }

    updateButtonStates();

    prevButton.addEventListener('click', function() {
        if (currentPage > 0) {
            goToPage(currentPage - 1);
        }
    });

    nextButton.addEventListener('click', function() {
        if (currentPage < totalPages - 1) {
            goToPage(currentPage + 1);
        }
    });

    window.addEventListener('resize', function() {
        cardWidth = updateCardWidth();
        goToPage(currentPage);
    });
});

window.addEventListener('DOMContentLoaded', () => {
  const pixelRatio = window.devicePixelRatio;
  const tables = document.querySelectorAll('.standingsTable');

  tables.forEach((table) => {
    if (pixelRatio === 1) {
      table.classList.add('table-vh-1')
    } else if (pixelRatio === 1.25) {
      table.classList.add('table-vh-1_25')
    }
  });
});

window.addEventListener('DOMContentLoaded', () => {
  const pixelRatio = window.devicePixelRatio;
  const tables = document.querySelectorAll('.playerTable');

  tables.forEach((table) => {
    if (pixelRatio === 1) {
      table.classList.add('table-vh-1')
    } else if (pixelRatio === 1.25) {
      table.classList.add('table-vh-1_25')
    }
  });
});

window.addEventListener('DOMContentLoaded', () => {
  const pixelRatio = window.devicePixelRatio;
  const boxscoreTables = document.querySelectorAll('.boxscore');

  boxscoreTables.forEach((table) => {
    // Check if device is running at 125% zoom (pixel ratio around 1.25)
    if (pixelRatio >= 1.24 && pixelRatio <= 1.26) {
      table.classList.remove('boxscore');
      table.classList.add('boxscore-scaled');
    }
  });
});