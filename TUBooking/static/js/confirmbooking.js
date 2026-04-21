document.addEventListener('DOMContentLoaded', function () {
    const typeSubject = document.getElementById('type_subject');
    const typeTutoring = document.getElementById('type_tutoring');
    const subjectFields = document.getElementById('subject_fields');
    const tutoringFields = document.getElementById('tutoring_fields');
    const selectAllDays = document.getElementById('select_all_days');
    const bookingForm = document.getElementById('bookingForm');

    // Get all day checkboxes (from subject form rendered in #days_checkboxes)
    const dayCheckboxes = document.querySelectorAll('#days_checkboxes input[type="checkbox"]');

    // Shared fields that need to be synced from subject- prefix to tutoring- prefix
    const sharedFields = ['date_start', 'date_end', 'time_start', 'time_end'];

    // ----- Toggle booking type -----
    function toggleFields() {
        if (typeSubject.checked) {
            subjectFields.style.display = 'block';
            tutoringFields.style.display = 'none';
            setFieldsDisabled(tutoringFields, true);
            setFieldsDisabled(subjectFields, false);
        } else {
            subjectFields.style.display = 'none';
            tutoringFields.style.display = 'block';
            setFieldsDisabled(subjectFields, true);
            setFieldsDisabled(tutoringFields, false);
        }
    }

    function setFieldsDisabled(container, disabled) {
        container.querySelectorAll('input, select, textarea').forEach(function (el) {
            el.disabled = disabled;
        });
    }

    typeSubject.addEventListener('change', toggleFields);
    typeTutoring.addEventListener('change', toggleFields);

    // ----- "everyday" toggle -----
    selectAllDays.addEventListener('change', function () {
        dayCheckboxes.forEach(function (cb) {
            cb.checked = selectAllDays.checked;
        });
    });

    dayCheckboxes.forEach(function (cb) {
        cb.addEventListener('change', function () {
            selectAllDays.checked = Array.from(dayCheckboxes).every(function (c) {
                return c.checked;
            });
        });
    });

    // ----- Sync shared fields on form submit -----
    if (bookingForm) {
        bookingForm.addEventListener('submit', function (e) {
            // Only sync when tutoring is selected
            if (!typeTutoring.checked) return;

            // Remove any previously created hidden sync inputs
            bookingForm.querySelectorAll('.tutoring-sync-field').forEach(function (el) {
                el.remove();
            });

            // Sync simple fields (date_start, date_end, time_start, time_end)
            sharedFields.forEach(function (fieldName) {
                var sourceEl = document.getElementById('id_subject-' + fieldName);
                if (sourceEl) {
                    var hidden = document.createElement('input');
                    hidden.type = 'hidden';
                    hidden.name = 'tutoring-' + fieldName;
                    hidden.value = sourceEl.value;
                    hidden.className = 'tutoring-sync-field';
                    bookingForm.appendChild(hidden);
                }
            });

            // Sync days_of_week checkboxes: copy checked subject- days as tutoring- days
            dayCheckboxes.forEach(function (cb) {
                if (cb.checked) {
                    var hidden = document.createElement('input');
                    hidden.type = 'hidden';
                    hidden.name = 'tutoring-days_of_week';
                    hidden.value = cb.value;
                    hidden.className = 'tutoring-sync-field';
                    bookingForm.appendChild(hidden);
                }
            });
        });
    }

    // Initial state
    toggleFields();
});

