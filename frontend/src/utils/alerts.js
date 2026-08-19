import Swal from 'sweetalert2'

const base = {
  confirmButtonColor: '#3182CE',
  cancelButtonColor: '#718096',
  buttonsStyling: true,
}

export function showSuccess(title, text) {
  return Swal.fire({ ...base, icon: 'success', title, text, timer: 1800, showConfirmButton: false })
}

export function showError(title, text) {
  return Swal.fire({ ...base, icon: 'error', title, text })
}

export function confirmAction(title, text, confirmText = 'Confirm') {
  return Swal.fire({
    ...base,
    icon: 'warning',
    title,
    text,
    showCancelButton: true,
    confirmButtonText: confirmText,
    cancelButtonText: 'Cancel',
  }).then(result => result.isConfirmed)
}
