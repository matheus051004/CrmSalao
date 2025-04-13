document.addEventListener('DOMContentLoaded', function () {
    // Funcionalidade de toggle da sidebar
    const body = document.body;
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
    const mobileToggle = document.getElementById('mobileToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    // Toggle para dispositivos desktop
    if (sidebarCollapseBtn) {
        sidebarCollapseBtn.addEventListener('click', function () {
            body.classList.toggle('sidebar-collapsed');

            // Muda o ícone do botão
            const icon = this.querySelector('i');
            if (body.classList.contains('sidebar-collapsed')) {
                icon.classList.remove('fa-chevron-left');
                icon.classList.add('fa-chevron-right');
            } else {
                icon.classList.remove('fa-chevron-right');
                icon.classList.add('fa-chevron-left');
            }
        });
    }

    // Toggle para dispositivos móveis
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function () {
            body.classList.toggle('sidebar-expanded');
        });
    }

    if (mobileToggle) {
        mobileToggle.addEventListener('click', function () {
            body.classList.toggle('sidebar-expanded');
        });
    }

    // Fechar sidebar ao clicar no overlay
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function () {
            body.classList.remove('sidebar-expanded');
        });
    }

    // Adiciona um listener para o botão de deletar
    const deleteButtons = document.querySelectorAll('.btn-danger[data-bs-toggle="modal"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function () {
            const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
            deleteModal.show();
        });
    });

    // Ajusta os gráficos ao redimensionar a janela
    window.addEventListener('resize', function () {
        leadsChart.resize();
        statusChart.resize();
    });
});
