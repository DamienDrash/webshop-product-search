document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.querySelector('#search-input');
    const searchResults = document.querySelector('#search-results');

    function search() {
        // Suchanfrage an Server senden und Ergebnisse abrufen
        fetch(`http://127.0.0.1:5000/search?query=${searchInput.value}`)
            .then(response => response.json())
            .then(results => {
                // Ergebnisse anzeigen
                searchResults.innerHTML = '';
                for (const result of results) {
                    searchResults.innerHTML += `
          <div class="result">
            <h3>${result.name}</h3>
            <p>${result.price}</p>
          </div>
        `;
                }
            });
    }

// Beim Eingeben in die Suchleiste die Funktion search aufrufen
    searchInput.addEventListener('input', search);
});
