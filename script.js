const sidebar = document.getElementById('sidebar');

function toggleSidebar() {
    sidebar.classList.toggle('closed');
}

document.addEventListener('DOMContentLoaded', () => {
    const menuToggle = document.createElement('button');
    menuToggle.textContent = '☰'; // Icona del menu
    menuToggle.addEventListener('click', toggleSidebar);
    document.body.insertBefore(menuToggle, document.body.firstChild);
});
