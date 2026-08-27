(function () {
    "use strict";

    const API_BASE = "/api/v1";
    const MAX_UPLOAD_SIZE = 5 * 1024 * 1024;
    const DEFAULT_CENTER = [121.4737, 31.2304];
    const DEFAULT_ZOOM = 11;
    const STATUS_LABELS = {
        carrier: "物品已取",
        notget: "物品未取",
    };

    const state = {
        map: null,
        mapReady: false,
        infoWindow: null,
        routes: [],
        activeRouteId: null,
        selectedRouteIds: new Set(),
        routeDetails: new Map(),
        detailRequests: new Map(),
        routeLayers: new Map(),
    };

    const dom = {
        map: document.getElementById("map"),
        mapConfig: document.getElementById("map-config"),
        mapState: document.getElementById("map-state"),
        mapStateTitle: document.getElementById("map-state-title"),
        mapStateMessage: document.getElementById("map-state-message"),
        globalStatus: document.getElementById("global-status"),
        importForm: document.getElementById("import-form"),
        routeFile: document.getElementById("route-file"),
        routeName: document.getElementById("route-name"),
        importSubmit: document.getElementById("import-submit"),
        importFeedback: document.getElementById("import-feedback"),
        refreshRoutes: document.getElementById("refresh-routes"),
        routeListLoading: document.getElementById("route-list-loading"),
        routeListEmpty: document.getElementById("route-list-empty"),
        routeListItems: document.getElementById("route-list-items"),
        detailLoading: document.getElementById("detail-loading"),
        detailEmpty: document.getElementById("detail-empty"),
        pointsTableContainer: document.getElementById("points-table-container"),
        pointsTableBody: document.getElementById("points-table-body"),
        activeRouteName: document.getElementById("active-route-name"),
        deleteRoute: document.getElementById("delete-route"),
        fitRoutes: document.getElementById("fit-routes"),
        visibleRouteCount: document.getElementById("visible-route-count"),
    };

    function readMapConfig() {
        try {
            return JSON.parse(dom.mapConfig.textContent || "{}");
        } catch (error) {
            return {};
        }
    }

    const mapConfig = readMapConfig() || {};

    function setMapState(stateName, title, message) {
        if (stateName === "ready") {
            dom.mapState.hidden = true;
            return;
        }

        dom.mapState.hidden = false;
        dom.mapState.dataset.state = stateName;
        dom.mapStateTitle.textContent = title;
        dom.mapStateMessage.textContent = message;
    }

    function setStatus(message, stateName) {
        dom.globalStatus.hidden = !message;
        dom.globalStatus.textContent = message || "";
        if (stateName) {
            dom.globalStatus.dataset.state = stateName;
        } else {
            delete dom.globalStatus.dataset.state;
        }
    }

    function setFeedback(message, stateName) {
        dom.importFeedback.hidden = !message;
        dom.importFeedback.textContent = message || "";
        if (stateName) {
            dom.importFeedback.dataset.state = stateName;
        } else {
            delete dom.importFeedback.dataset.state;
        }
    }

    function setButtonBusy(button, busy, busyText) {
        if (!button) {
            return;
        }

        if (busy) {
            button.dataset.previousText = button.textContent;
            button.textContent = busyText;
            button.disabled = true;
        } else {
            button.textContent = button.dataset.previousText || button.textContent;
            delete button.dataset.previousText;
            button.disabled = false;
        }
    }

    function getCsrfToken() {
        const tokenInput = document.querySelector(
            "input[name='csrfmiddlewaretoken']",
        );
        if (tokenInput && tokenInput.value) {
            return tokenInput.value;
        }

        const cookie = document.cookie
            .split(";")
            .map((item) => item.trim())
            .find((item) => item.startsWith("csrftoken="));
        return cookie ? decodeURIComponent(cookie.slice("csrftoken=".length)) : "";
    }

    async function requestJson(url, options) {
        const requestOptions = options || {};
        const headers = new Headers(requestOptions.headers || {});
        if (!headers.has("Accept")) {
            headers.set("Accept", "application/json");
        }

        const response = await fetch(url, {
            ...requestOptions,
            headers,
            credentials: "same-origin",
        });

        let payload = null;
        try {
            payload = await response.json();
        } catch (error) {
            payload = null;
        }

        if (!response.ok) {
            const apiError = new Error(
                payload && payload.error && payload.error.message
                    ? payload.error.message
                    : `请求失败（HTTP ${response.status}）`,
            );
            apiError.status = response.status;
            apiError.payload = payload;
            throw apiError;
        }

        return payload;
    }

    function formatApiError(error) {
        const apiError = error && error.payload && error.payload.error;
        if (!apiError) {
            const message = error && error.message ? error.message : "请求失败，请稍后重试。";
            return error && error.status === 403
                ? `${message}\n请求被 CSRF 安全检查拒绝，请刷新页面后重试。`
                : message;
        }

        const lines = [apiError.message || "请求失败。"];
        if (Array.isArray(apiError.details)) {
            apiError.details.forEach((detail) => {
                const linePrefix = detail.line ? `第 ${detail.line} 行：` : "";
                lines.push(`${linePrefix}${detail.message || detail.code || "数据无效"}`);
            });
        }
        if (error.status === 403) {
            lines.push("请求被 CSRF 安全检查拒绝，请刷新页面后重试。");
        }
        return lines.join("\n");
    }

    function getSafeRouteColor(color) {
        return /^#[0-9a-f]{6}$/i.test(color || "") ? color : "#1769aa";
    }

    function getRoute(routeId) {
        return state.routes.find((route) => Number(route.id) === Number(routeId)) || null;
    }

    function getRouteDetail(routeId) {
        return state.routeDetails.get(Number(routeId)) || null;
    }

    function getStatusLabel(status) {
        return STATUS_LABELS[status] || "未知状态";
    }

    function formatCoordinate(value) {
        const number = Number(value);
        return Number.isFinite(number) ? number.toFixed(6) : "-";
    }

    function renderRouteList() {
        const fragment = document.createDocumentFragment();

        state.routes.forEach((route) => {
            const routeId = Number(route.id);
            const item = document.createElement("li");
            item.className = "route-item";
            item.dataset.routeId = String(routeId);
            if (routeId === Number(state.activeRouteId)) {
                item.classList.add("is-active");
            }

            const checkbox = document.createElement("input");
            checkbox.className = "route-check";
            checkbox.type = "checkbox";
            checkbox.checked = state.selectedRouteIds.has(routeId);
            checkbox.setAttribute("aria-label", `在地图上显示${route.name}`);
            checkbox.addEventListener("change", () => {
                toggleRoute(routeId, checkbox.checked);
            });

            const selectButton = document.createElement("button");
            selectButton.className = "route-select";
            selectButton.type = "button";
            selectButton.setAttribute(
                "aria-pressed",
                routeId === Number(state.activeRouteId) ? "true" : "false",
            );
            selectButton.addEventListener("click", () => {
                setActiveRoute(routeId);
            });

            const swatch = document.createElement("span");
            swatch.className = "route-swatch";
            swatch.style.backgroundColor = getSafeRouteColor(route.color);
            swatch.setAttribute("aria-hidden", "true");

            const name = document.createElement("span");
            name.className = "route-name";
            name.textContent = route.name;

            selectButton.append(swatch, name);

            const meta = document.createElement("span");
            meta.className = "route-meta";
            meta.textContent = `${route.point_count} 个点`;

            item.append(checkbox, selectButton, meta);
            fragment.append(item);
        });

        dom.routeListItems.replaceChildren(fragment);
        dom.routeListItems.hidden = state.routes.length === 0;
        dom.routeListEmpty.hidden = state.routes.length !== 0;
    }

    function renderPointTable() {
        const route = getRoute(state.activeRouteId);
        const detail = getRouteDetail(state.activeRouteId);

        dom.activeRouteName.textContent = route ? route.name : "";
        dom.deleteRoute.hidden = !route;

        if (!route) {
            dom.detailLoading.hidden = true;
            dom.detailEmpty.hidden = false;
            dom.pointsTableContainer.hidden = true;
            dom.pointsTableBody.replaceChildren();
            return;
        }

        if (!detail) {
            dom.detailLoading.hidden = false;
            dom.detailEmpty.hidden = true;
            dom.pointsTableContainer.hidden = true;
            dom.pointsTableBody.replaceChildren();
            return;
        }

        const points = Array.isArray(detail.points) ? detail.points : [];
        const fragment = document.createDocumentFragment();

        points.forEach((point) => {
            const row = document.createElement("tr");
            row.tabIndex = 0;
            row.setAttribute(
                "aria-label",
                `第 ${point.sequence} 个轨迹点，${getStatusLabel(point.status)}`,
            );
            row.addEventListener("click", () => {
                focusPoint(route.id, point.id);
            });
            row.addEventListener("keydown", (event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    focusPoint(route.id, point.id);
                }
            });

            const sequenceCell = document.createElement("td");
            sequenceCell.textContent = String(point.sequence);

            const statusCell = document.createElement("td");
            const status = document.createElement("span");
            status.className = `point-status point-status--${point.status === "carrier" ? "carrier" : "notget"}`;
            status.textContent = getStatusLabel(point.status);
            statusCell.append(status);

            const locationCell = document.createElement("td");
            const location = document.createElement("span");
            location.className = "point-location";
            location.textContent = `${formatCoordinate(point.longitude)}, ${formatCoordinate(point.latitude)}`;
            const description = document.createElement("span");
            description.className = "point-description";
            description.textContent = point.description || "无说明";
            locationCell.append(location, description);

            row.append(sequenceCell, statusCell, locationCell);
            fragment.append(row);
        });

        dom.pointsTableBody.replaceChildren(fragment);
        dom.detailLoading.hidden = true;
        dom.detailEmpty.hidden = points.length !== 0;
        dom.pointsTableContainer.hidden = points.length === 0;
    }

    function updateVisibleRouteCount() {
        dom.visibleRouteCount.textContent = `${state.selectedRouteIds.size} 条路径`;
    }

    function removeRouteLayer(routeId) {
        const numericRouteId = Number(routeId);
        const layer = state.routeLayers.get(numericRouteId);
        if (!layer) {
            return;
        }

        if (state.map) {
            state.map.remove(layer.overlays);
        }
        if (state.infoWindow) {
            state.infoWindow.close();
        }
        state.routeLayers.delete(numericRouteId);
    }

    function createMarkerContent(route, point) {
        const markerContent = document.createElement("div");
        markerContent.className = `route-marker route-marker--${point.status === "carrier" ? "carrier" : "notget"}`;
        markerContent.style.setProperty("--route-color", getSafeRouteColor(route.color));
        markerContent.textContent = point.status === "carrier" ? "取" : "待";
        markerContent.setAttribute(
            "aria-label",
            `第 ${point.sequence} 个轨迹点，${getStatusLabel(point.status)}`,
        );
        return markerContent;
    }

    function appendInfoRow(container, label, value) {
        const row = document.createElement("div");
        row.className = "map-info-row";
        const labelElement = document.createElement("span");
        labelElement.className = "map-info-label";
        labelElement.textContent = label;
        const valueElement = document.createElement("span");
        valueElement.className = "map-info-value";
        valueElement.textContent = value;
        row.append(labelElement, valueElement);
        container.append(row);
    }

    function createInfoWindowContent(route, point) {
        const container = document.createElement("div");
        container.className = "map-info-window";
        const title = document.createElement("p");
        title.className = "map-info-title";
        title.textContent = route.name;
        container.append(title);
        appendInfoRow(container, "轨迹点", `第 ${point.sequence} 个`);
        appendInfoRow(container, "状态", getStatusLabel(point.status));
        appendInfoRow(
            container,
            "坐标",
            `${formatCoordinate(point.longitude)}, ${formatCoordinate(point.latitude)}`,
        );
        appendInfoRow(container, "说明", point.description || "无说明");
        return container;
    }

    function openPointInfo(route, point, marker) {
        if (!state.infoWindow || !state.map) {
            return;
        }

        state.infoWindow.setContent(createInfoWindowContent(route, point));
        state.infoWindow.open(state.map, marker.getPosition());
    }

    function drawRoute(routeId) {
        if (!state.map || !state.mapReady) {
            return;
        }

        const route = getRoute(routeId);
        const detail = getRouteDetail(routeId);
        if (!route || !detail || !Array.isArray(detail.points)) {
            return;
        }

        removeRouteLayer(routeId);
        const numericRouteId = Number(routeId);
        const points = [...detail.points].sort(
            (left, right) => Number(left.sequence) - Number(right.sequence),
        );
        const path = points
            .map((point) => [Number(point.longitude), Number(point.latitude)])
            .filter((position) => position.every((value) => Number.isFinite(value)));
        const overlays = [];

        if (path.length >= 2) {
            const polyline = new window.AMap.Polyline({
                path,
                strokeColor: getSafeRouteColor(route.color),
                strokeWeight: 5,
                strokeOpacity: 0.86,
                lineJoin: "round",
                showDir: true,
                zIndex: 20,
            });
            overlays.push(polyline);
        }

        const markerMap = new Map();
        points.forEach((point, index) => {
            const longitude = Number(point.longitude);
            const latitude = Number(point.latitude);
            if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) {
                return;
            }

            const marker = new window.AMap.Marker({
                position: [longitude, latitude],
                content: createMarkerContent(route, point),
                offset: new window.AMap.Pixel(-14, -14),
                zIndex: 100 + index,
            });
            marker.on("mouseover", () => {
                openPointInfo(route, point, marker);
            });
            marker.on("mouseout", () => {
                window.setTimeout(() => {
                    if (state.infoWindow) {
                        state.infoWindow.close();
                    }
                }, 120);
            });
            marker.on("click", () => {
                setActiveRoute(route.id);
                openPointInfo(route, point, marker);
            });
            markerMap.set(String(point.id), marker);
            overlays.push(marker);
        });

        if (overlays.length > 0) {
            state.map.add(overlays);
        }
        state.routeLayers.set(numericRouteId, {
            overlays,
            markers: markerMap,
        });
    }

    function syncRouteLayers() {
        if (!state.mapReady) {
            return;
        }

        state.routeLayers.forEach((layer, routeId) => {
            if (!state.selectedRouteIds.has(routeId)) {
                removeRouteLayer(routeId);
            }
        });

        state.selectedRouteIds.forEach((routeId) => {
            if (getRouteDetail(routeId)) {
                drawRoute(routeId);
            }
        });
    }

    function fitMapToVisibleRoutes() {
        if (!state.map || !state.mapReady) {
            return;
        }

        const overlays = [];
        state.selectedRouteIds.forEach((routeId) => {
            const layer = state.routeLayers.get(routeId);
            if (layer) {
                overlays.push(...layer.overlays);
            }
        });

        if (overlays.length > 0) {
            state.map.setFitView(overlays, false, [50, 50, 50, 50]);
            return;
        }

        state.map.setCenter(DEFAULT_CENTER);
        state.map.setZoom(DEFAULT_ZOOM);
    }

    async function ensureRouteDetail(routeId) {
        const numericRouteId = Number(routeId);
        if (state.routeDetails.has(numericRouteId)) {
            return state.routeDetails.get(numericRouteId);
        }
        if (state.detailRequests.has(numericRouteId)) {
            return state.detailRequests.get(numericRouteId);
        }

        const request = requestJson(`${API_BASE}/routes/${numericRouteId}/`)
            .then((payload) => {
                const detail = payload && payload.data ? payload.data : null;
                if (!detail) {
                    throw new Error("路径详情响应格式错误");
                }
                state.routeDetails.set(numericRouteId, detail);
                renderPointTable();
                syncRouteLayers();
                fitMapToVisibleRoutes();
                return detail;
            })
            .catch((error) => {
                if (Number(state.activeRouteId) === numericRouteId) {
                    renderPointTable();
                    setStatus(`读取路径“${getRoute(numericRouteId)?.name || ""}”失败：${formatApiError(error)}`, "error");
                }
                throw error;
            })
            .finally(() => {
                state.detailRequests.delete(numericRouteId);
            });

        state.detailRequests.set(numericRouteId, request);
        return request;
    }

    function setActiveRoute(routeId) {
        const route = getRoute(routeId);
        if (!route) {
            return;
        }

        state.activeRouteId = Number(route.id);
        state.selectedRouteIds.add(Number(route.id));
        renderRouteList();
        renderPointTable();
        updateVisibleRouteCount();
        syncRouteLayers();
        void ensureRouteDetail(route.id).catch(() => undefined);
        fitMapToVisibleRoutes();
    }

    function toggleRoute(routeId, checked) {
        const numericRouteId = Number(routeId);
        if (checked) {
            state.selectedRouteIds.add(numericRouteId);
            if (state.activeRouteId === null) {
                state.activeRouteId = numericRouteId;
            }
            void ensureRouteDetail(numericRouteId).catch(() => undefined);
        } else {
            state.selectedRouteIds.delete(numericRouteId);
            removeRouteLayer(numericRouteId);
        }

        renderRouteList();
        renderPointTable();
        updateVisibleRouteCount();
        syncRouteLayers();
        fitMapToVisibleRoutes();
    }

    async function loadRoutes(preferredRouteId) {
        dom.routeListLoading.hidden = false;
        dom.routeListEmpty.hidden = true;

        try {
            const payload = await requestJson(`${API_BASE}/routes/`);
            const results = payload && payload.data && Array.isArray(payload.data.results)
                ? payload.data.results
                : [];
            state.routes = results;
            const validRouteIds = new Set(results.map((route) => Number(route.id)));

            state.selectedRouteIds.forEach((routeId) => {
                if (!validRouteIds.has(routeId)) {
                    state.selectedRouteIds.delete(routeId);
                    removeRouteLayer(routeId);
                    state.routeDetails.delete(routeId);
                }
            });

            if (preferredRouteId !== undefined && validRouteIds.has(Number(preferredRouteId))) {
                state.activeRouteId = Number(preferredRouteId);
                state.selectedRouteIds.add(Number(preferredRouteId));
            } else if (!validRouteIds.has(Number(state.activeRouteId))) {
                state.activeRouteId = results.length > 0 ? Number(results[0].id) : null;
            }

            if (state.activeRouteId !== null && state.routes.length > 0) {
                state.selectedRouteIds.add(Number(state.activeRouteId));
            }

            renderRouteList();
            renderPointTable();
            updateVisibleRouteCount();
            syncRouteLayers();

            if (state.activeRouteId !== null) {
                void ensureRouteDetail(state.activeRouteId).catch(() => undefined);
            }
            state.selectedRouteIds.forEach((routeId) => {
                void ensureRouteDetail(routeId).catch(() => undefined);
            });
            fitMapToVisibleRoutes();
            return true;
        } catch (error) {
            renderRouteList();
            setStatus(`读取路径列表失败：${formatApiError(error)}`, "error");
            return false;
        } finally {
            dom.routeListLoading.hidden = true;
            if (state.routes.length === 0) {
                dom.routeListEmpty.hidden = false;
            }
        }
    }

    function focusPoint(routeId, pointId) {
        const layer = state.routeLayers.get(Number(routeId));
        const marker = layer && layer.markers.get(String(pointId));
        if (!marker || !state.map) {
            return;
        }

        const position = marker.getPosition();
        state.map.setCenter(position);
        state.map.setZoom(Math.max(state.map.getZoom(), 15));
        const route = getRoute(routeId);
        const detail = getRouteDetail(routeId);
        const point = detail && Array.isArray(detail.points)
            ? detail.points.find((item) => String(item.id) === String(pointId))
            : null;
        if (route && point) {
            openPointInfo(route, point, marker);
        }
    }

    async function handleImport(event) {
        event.preventDefault();
        const file = dom.routeFile.files && dom.routeFile.files[0];
        if (!file) {
            setFeedback("请选择一个 TXT 路径文件。", "error");
            return;
        }
        if (!file.name.toLowerCase().endsWith(".txt")) {
            setFeedback("只允许上传 TXT 文件。", "error");
            return;
        }
        if (file.size > MAX_UPLOAD_SIZE) {
            setFeedback("文件大小不能超过 5 MB。", "error");
            return;
        }

        const formData = new FormData(dom.importForm);
        setButtonBusy(dom.importSubmit, true, "导入中...");
        setFeedback("正在解析并保存路径...", "info");
        try {
            const payload = await requestJson(`${API_BASE}/routes/import/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCsrfToken(),
                },
                body: formData,
            });
            const data = payload && payload.data ? payload.data : {};
            const warningCount = Array.isArray(data.warnings) ? data.warnings.length : 0;
            let message = `导入成功：${data.name || "未命名路径"}，共 ${data.point_count || 0} 个轨迹点。`;
            if (warningCount > 0) {
                const warningText = data.warnings
                    .map((warning) => `第 ${warning.line} 行：${warning.message}`)
                    .join("\n");
                message += `\n发现 ${warningCount} 条提示：\n${warningText}`;
            }
            setFeedback(message, warningCount > 0 ? "warning" : "success");
            dom.importForm.reset();
            await loadRoutes(data.id);
        } catch (error) {
            setFeedback(formatApiError(error), "error");
        } finally {
            setButtonBusy(dom.importSubmit, false, "导入路径");
        }
    }

    async function handleDelete() {
        const route = getRoute(state.activeRouteId);
        if (!route) {
            return;
        }
        if (!window.confirm(`确定删除路径“${route.name}”及其全部轨迹点吗？`)) {
            return;
        }

        setButtonBusy(dom.deleteRoute, true, "删除中...");
        try {
            await requestJson(`${API_BASE}/routes/${route.id}/`, {
                method: "DELETE",
                headers: {
                    "X-CSRFToken": getCsrfToken(),
                },
            });
            state.routeDetails.delete(Number(route.id));
            state.selectedRouteIds.delete(Number(route.id));
            removeRouteLayer(route.id);
            state.activeRouteId = null;
            setFeedback(`已删除路径“${route.name}”。`, "success");
            await loadRoutes();
        } catch (error) {
            setStatus(`删除路径失败：${formatApiError(error)}`, "error");
        } finally {
            setButtonBusy(dom.deleteRoute, false, "删除当前路径");
        }
    }

    function loadAmapScript() {
        if (!mapConfig.amap_js_key) {
            return Promise.reject(new Error("未配置高德地图 JavaScript API Key"));
        }
        if (window.AMap) {
            return Promise.resolve(window.AMap);
        }
        if (mapConfig.amap_security_js_code) {
            window._AMapSecurityConfig = {
                securityJsCode: mapConfig.amap_security_js_code,
            };
        }

        return new Promise((resolve, reject) => {
            const existingScript = document.querySelector("script[data-amap-sdk]");
            if (existingScript) {
                existingScript.addEventListener("load", () => resolve(window.AMap));
                existingScript.addEventListener("error", () => reject(new Error("高德地图脚本加载失败")));
                return;
            }

            const script = document.createElement("script");
            script.dataset.amapSdk = "true";
            script.async = true;
            script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(mapConfig.amap_js_key)}&plugin=AMap.Scale,AMap.ToolBar`;
            script.onload = () => {
                if (window.AMap) {
                    resolve(window.AMap);
                } else {
                    reject(new Error("高德地图脚本未提供地图对象"));
                }
            };
            script.onerror = () => reject(new Error("高德地图脚本加载失败，请检查 Key 和网络连接"));
            document.head.append(script);
        });
    }

    function initializeMap() {
        state.map = new window.AMap.Map(dom.map, {
            center: DEFAULT_CENTER,
            zoom: DEFAULT_ZOOM,
            resizeEnable: true,
        });
        if (window.AMap.Scale) {
            state.map.addControl(new window.AMap.Scale());
        }
        if (window.AMap.ToolBar) {
            state.map.addControl(new window.AMap.ToolBar({ position: "RB" }));
        }
        state.infoWindow = new window.AMap.InfoWindow({
            offset: new window.AMap.Pixel(0, -18),
            closeWhenClickMap: true,
        });
        state.mapReady = true;
        setMapState("ready");
    }

    function bindEvents() {
        dom.importForm.addEventListener("submit", handleImport);
        dom.refreshRoutes.addEventListener("click", () => {
            void loadRoutes();
        });
        dom.fitRoutes.addEventListener("click", fitMapToVisibleRoutes);
        dom.deleteRoute.addEventListener("click", () => {
            void handleDelete();
        });
    }

    async function initialize() {
        bindEvents();
        if (!mapConfig.amap_js_key) {
            setMapState(
                "error",
                "地图密钥未配置",
                "请在本地 .env 中设置 AMAP_JS_KEY，路径列表仍可正常使用。",
            );
            await loadRoutes();
            return;
        }

        try {
            await loadAmapScript();
            initializeMap();
        } catch (error) {
            setMapState("error", "地图加载失败", error.message);
            setStatus(`地图暂不可用：${error.message}`, "error");
        }
        await loadRoutes();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initialize, { once: true });
    } else {
        void initialize();
    }
})();
