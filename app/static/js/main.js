// Live search
const searchInput = document.getElementById('live-search');
if (searchInput) {
    searchInput.addEventListener('input', function() {
        fetch(`/search?q=${encodeURIComponent(this.value)}`)
            .then(res => res.text())
            .then(html => {
                document.getElementById('search-results').innerHTML = html;
            });
    });
}
// Language toggle (reloads page)
document.querySelectorAll('.lang-toggle a').forEach(el => {
    el.addEventListener('click', function(e) {
        e.preventDefault();
        fetch(this.href)
            .then(() => location.reload());
    });
});
