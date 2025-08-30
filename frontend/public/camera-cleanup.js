
window.addEventListener('beforeunload', function() {
  // Stop all camera streams
  navigator.mediaDevices.getUserMedia({video: true}).then(stream => {
    stream.getTracks().forEach(track => track.stop());
  }).catch(() => {});
});

window.addEventListener('pagehide', function() {
  // Force stop all media streams
  if(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.enumerateDevices().then(devices => {
      devices.forEach(device => {
        if(device.kind === 'videoinput') {
          console.log('Forcing camera stop');
        }
      });
    });
  }
});

