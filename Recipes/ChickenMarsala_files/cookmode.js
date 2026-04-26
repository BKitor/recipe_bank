jQuery(document).ready(function() {
    var cookModeWakeLock = {
        api: false,
        wakelock: false,
        init() {
            if ('wakeLock' in navigator && 'request' in navigator.wakeLock) {
                this.api = navigator.wakeLock;
                var wakelockvar = this;
                jQuery('.cookmode').on('click','button',function() {
                    var enabled = jQuery(this).attr('aria-pressed')==='true';
                    if (enabled) wakelockvar.unlock();
                    else wakelockvar.lock();
                });
                jQuery('.cookmode').show();		
            }
        },
        setToggle(enabled) {
            if (enabled) jQuery('.cookmode button').attr('aria-pressed',true);
            else jQuery('.cookmode button').attr('aria-pressed',false);
        },
        async lock() {
            try {
                this.wakelock = await this.api.request('screen');
                this.wakelock.addEventListener('release',function() {
                    this.wakelock = false;
                    this.setToggle(false);
                });
                this.setToggle(true);
            } catch (e) {      
                this.setToggle(false);
            }		
        },
        unlock() {
            if ( this.wakelock ) {
                this.wakelock.release();
                this.wakelock = false;
            }
            this.setToggle(false);
        }	
    };

    cookModeWakeLock.init();
});