function MissionControl({
    missions = [],
    onUpdateStatus,
    onSelectMission,
    selectedMissionId
}) {

    const getNextStatus = (currentStatus) => {
        switch (currentStatus) {
            case "ASSIGNED":
            case "DISPATCHED":
                return "EN_ROUTE";
            case "EN_ROUTE":
                return "ARRIVED";
            case "ARRIVED":
                return "COMPLETED";
            default:
                return "COMPLETED";
        }
    };

    const getNextStatusLabel = (currentStatus) => {
        switch (currentStatus) {
            case "ASSIGNED":
            case "DISPATCHED":
                return "🚚 Mark En Route";
            case "EN_ROUTE":
                return "🎯 Mark Arrived";
            case "ARRIVED":
                return "✅ Complete Mission";
            default:
                return "✅ Complete Mission";
        }
    };

    const getStatusBadgeClass = (status) => {
        switch (status) {
            case "ASSIGNED":
                return "status-assigned";
            case "DISPATCHED":
                return "status-dispatched";
            case "EN_ROUTE":
                return "status-en-route";
            case "ARRIVED":
                return "status-arrived";
            case "COMPLETED":
                return "status-completed";
            default:
                return "status-default";
        }
    };

    return (
        <div className="mission-control-panel">

            <div className="section-title">
                <span>🚨</span>
                <h2>Active Mission Control</h2>
            </div>

            {missions.length === 0 ? (
                <div className="no-missions">
                    <p>No active rescue missions currently in progress.</p>
                    <span className="sub-text">Dispatch a rescue team from an active disaster to initiate a mission.</span>
                </div>
            ) : (
                <div className="missions-list">
                    {missions.map(mission => {
                        const isSelected = selectedMissionId === mission.assignment_id;

                        return (
                            <div
                                key={mission.assignment_id}
                                className={`mission-card ${isSelected ? "selected-mission" : ""}`}
                            >
                                <div className="mission-header">
                                    <div className="mission-title">
                                        <h3>🚨 {mission.disaster.title}</h3>
                                        <span className={`severity-badge ${mission.disaster.severity.toLowerCase()}`}>
                                            {mission.disaster.severity}
                                        </span>
                                    </div>
                                    <span className={`mission-status-badge ${getStatusBadgeClass(mission.status)}`}>
                                        {mission.status}
                                    </span>
                                </div>

                                <div className="mission-body">
                                    <div className="mission-detail-row">
                                        <span>🚑 Response Team:</span>
                                        <strong>{mission.team.name}</strong>
                                    </div>

                                    <div className="mission-detail-row">
                                        <span>🚙 Vehicle & Crew:</span>
                                        <span>{mission.team.vehicle} ({mission.team.members} members)</span>
                                    </div>

                                    <div className="mission-route-stats">
                                        <div className="stat-pill">
                                            <span>🚗 Road Distance</span>
                                            <strong>{mission.distance_km} km</strong>
                                        </div>

                                        <div className="stat-pill">
                                            <span>⏱ Est. ETA</span>
                                            <strong>{mission.eta_minutes} min</strong>
                                        </div>
                                    </div>
                                </div>

                                <div className="mission-actions">
                                    {onSelectMission && (
                                        <button
                                            className="action-btn focus-btn"
                                            onClick={() => onSelectMission(mission)}
                                        >
                                            🗺️ Focus Route
                                        </button>
                                    )}

                                    {onUpdateStatus && mission.status !== "COMPLETED" && (
                                        <>
                                            <button
                                                className="action-btn progress-btn"
                                                onClick={() => onUpdateStatus(mission.assignment_id, getNextStatus(mission.status))}
                                            >
                                                {getNextStatusLabel(mission.status)}
                                            </button>

                                            {mission.status !== "ARRIVED" && (
                                                <button
                                                    className="action-btn complete-btn"
                                                    onClick={() => onUpdateStatus(mission.assignment_id, "COMPLETED")}
                                                >
                                                    ✅ Complete
                                                </button>
                                            )}
                                        </>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

export default MissionControl;