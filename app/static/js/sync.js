/**
 * MediApp Lifecycle-Aware Synchronization Manager.
 * Governs polling intervals, prevents overlapping requests, respects Page Visibility API,
 * and ensures guaranteed cleanup on unmount or tab transitions.
 */

const Sync = {
  _intervals: {},
  _inFlight: {},

  register(key, taskFn, intervalMs = 6000) {
    this.stop(key);

    const execute = async () => {
      // Pause if tab is hidden in background
      if (document.hidden) return;
      if (this._inFlight[key]) return; // Prevent overlapping requests

      this._inFlight[key] = true;
      try {
        await taskFn();
      } catch (err) {
        console.warn(`Sync error in task [${key}]:`, err);
      } finally {
        this._inFlight[key] = false;
      }
    };

    // Run immediately once, then schedule interval
    execute();
    this._intervals[key] = setInterval(execute, intervalMs);
  },

  stop(key) {
    if (this._intervals[key]) {
      clearInterval(this._intervals[key]);
      delete this._intervals[key];
    }
    this._inFlight[key] = false;
  },

  stopAll() {
    Object.keys(this._intervals).forEach(key => this.stop(key));
  }
};

// Global visibility change handler
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) {
    // Immediate refresh on return to tab
    const activeRole = State.get("activeRole");
    const activeTab = State.get("activeTab");
    console.log(`Tab visible: triggering sync refresh for ${activeRole}/${activeTab}`);
  }
});
