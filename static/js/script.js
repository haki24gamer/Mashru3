// Initialize tooltips and other Bootstrap components
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Initialize dropdowns
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'))
    var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
      return new bootstrap.Dropdown(dropdownToggleEl)
    });

    // Task dropdown functionality - update for Bootstrap 5
    const taskSubmenu = document.querySelector('#tasksSubmenu');
    if (taskSubmenu) {
        const taskDropdown = document.querySelector('[data-toggle="collapse"][href="#tasksSubmenu"]');
        if (taskDropdown) {
            taskDropdown.addEventListener('click', function(e) {
                e.preventDefault();
                const submenu = document.querySelector(this.getAttribute('href'));
                if (submenu) {
                    submenu.classList.toggle('show');
                    this.setAttribute('aria-expanded', submenu.classList.contains('show'));
                }
            });
        }
    }

    // Make project cards clickable
    const projectCards = document.querySelectorAll('.project-card');
    projectCards.forEach(function(card) {
        const projectLink = card.getAttribute('data-href');
        if (projectLink) {
            card.addEventListener('click', function() {
                window.location.href = projectLink;
            });
        }
    });
    
    // Fix for older Bootstrap data-toggle attributes
    document.querySelectorAll('[data-toggle="modal"]').forEach(function(el) {
        el.addEventListener('click', function() {
            var target = this.getAttribute('data-target');
            var modalElement = document.querySelector(target);
            if (modalElement) {
                var modal = new bootstrap.Modal(modalElement);
                modal.show();
            }
        });
    });
    
    document.querySelectorAll('[data-toggle="collapse"]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            e.preventDefault();
            var target = this.getAttribute('href');
            var collapseElement = document.querySelector(target);
            if (collapseElement) {
                var bsCollapse = new bootstrap.Collapse(collapseElement, {
                    toggle: true
                });
            }
        });
    });
    
    // Handle sidebar toggle
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function() {
            document.getElementById('sidebar').classList.toggle('active');
            document.getElementById('content').classList.toggle('active');
        });
    }
});