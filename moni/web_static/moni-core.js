(function () {
  function whenTHREE() {
    return new Promise(function (res) {
      (function check() {
        if (window.THREE) return res(window.THREE);
        setTimeout(check, 40);
      })();
    });
  }

  class MoniCore extends HTMLElement {
    connectedCallback() {
      if (this._booted) return;
      this._booted = true;
      this.style.display = 'block';
      this.style.width = this.style.width || '100%';
      this.style.height = this.style.height || '100%';
      this.style.cursor = 'grab';
      whenTHREE().then((T) => this._init(T));
    }

    disconnectedCallback() {
      cancelAnimationFrame(this._raf);
      if (this._ro) this._ro.disconnect();
      if (this._renderer) this._renderer.dispose();
    }

    _init(THREE) {
      const accent = new THREE.Color(this.getAttribute('accent') || '#9184d9');
      const accent2 = new THREE.Color(this.getAttribute('accent2') || '#b5abfc');

      const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
      renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
      renderer.domElement.style.display = 'block';
      this.appendChild(renderer.domElement);
      this._renderer = renderer;

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
      camera.position.set(0, 0.35, 5.4);

      const group = new THREE.Group();
      scene.add(group);

      const shell = new THREE.Mesh(
        new THREE.IcosahedronGeometry(1.30, 3),
        new THREE.MeshStandardMaterial({
          color: 0x2b2741, flatShading: true, metalness: 0.45, roughness: 0.32,
          emissive: accent.clone().multiplyScalar(0.14), transparent: true, opacity: 0.92
        })
      );
      shell.name = 'shell';
      group.add(shell);

      const edges = new THREE.LineSegments(
        new THREE.EdgesGeometry(new THREE.IcosahedronGeometry(1.315, 1)),
        new THREE.LineBasicMaterial({ color: accent2, transparent: true, opacity: 0.55 })
      );
      group.add(edges);

      const inner = new THREE.Mesh(
        new THREE.SphereGeometry(0.72, 22, 14),
        new THREE.MeshStandardMaterial({
          color: accent, emissive: accent, emissiveIntensity: 0.85,
          metalness: 0.1, roughness: 0.5, wireframe: true
        })
      );
      inner.name = 'kern';
      group.add(inner);

      const rings = new THREE.Group();
      [[1.95, 0.9, 0], [2.35, -0.5, 1.1]].forEach(function (r, i) {
        const ring = new THREE.Mesh(
          new THREE.TorusGeometry(r[0], 0.008, 8, 160),
          new THREE.MeshBasicMaterial({ color: i ? accent2 : accent, transparent: true, opacity: 0.5 })
        );
        ring.rotation.set(r[1], r[2], 0);
        rings.add(ring);
      });
      group.add(rings);

      const dustGeo = new THREE.BufferGeometry();
      const pts = [];
      for (let i = 0; i < 220; i++) {
        const t = Math.random() * Math.PI * 2, p = Math.acos(2 * Math.random() - 1), rr = 2.0 + Math.random() * 1.4;
        pts.push(rr * Math.sin(p) * Math.cos(t), rr * Math.cos(p) * 0.55, rr * Math.sin(p) * Math.sin(t));
      }
      dustGeo.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
      const dust = new THREE.Points(dustGeo, new THREE.PointsMaterial({ color: accent2, size: 0.022, transparent: true, opacity: 0.6 }));
      group.add(dust);

      scene.add(new THREE.AmbientLight(0x3a3f5c, 1.1));
      const key = new THREE.PointLight(accent, 1.5, 26); key.position.set(3.2, 2.6, 4);
      const fill = new THREE.PointLight(accent2, 0.9, 24); fill.position.set(-3.4, -1.6, -2.4);
      scene.add(key, fill);

      let vx = 0.0016, vy = 0.0042, dragging = false, lx = 0, ly = 0;
      const el = this;
      el.addEventListener('pointerdown', function (e) {
        dragging = true; lx = e.clientX; ly = e.clientY; el.style.cursor = 'grabbing';
        el.setPointerCapture(e.pointerId);
      });
      el.addEventListener('pointermove', function (e) {
        if (!dragging) return;
        vy = (e.clientX - lx) * 0.0045; vx = (e.clientY - ly) * 0.0045;
        group.rotation.y += vy; group.rotation.x += vx;
        lx = e.clientX; ly = e.clientY;
      });
      const stop = function () { dragging = false; el.style.cursor = 'grab'; };
      el.addEventListener('pointerup', stop);
      el.addEventListener('pointercancel', stop);

      const resize = function () {
        const w = el.clientWidth || 320, h = el.clientHeight || 320;
        renderer.setSize(w, h, false);
        renderer.domElement.style.width = w + 'px';
        renderer.domElement.style.height = h + 'px';
        camera.aspect = w / h; camera.updateProjectionMatrix();
      };
      this._ro = new ResizeObserver(resize); this._ro.observe(this); resize();

      const t0 = performance.now();
      const tick = function () {
        el._raf = requestAnimationFrame(tick);
        const t = (performance.now() - t0) / 1000;
        if (!dragging) {
          vy += (0.0042 - vy) * 0.03; vx += (0.0009 - vx) * 0.03;
          group.rotation.y += vy; group.rotation.x += vx;
        }
        inner.rotation.y -= 0.011; inner.rotation.x += 0.006;
        rings.rotation.z += 0.0016; rings.children[1].rotation.z -= 0.004;
        dust.rotation.y -= 0.0009;
        const b = 1 + Math.sin(t * 1.25) * 0.022;
        shell.scale.setScalar(b);
        inner.material.emissiveIntensity = 0.7 + Math.sin(t * 2.1) * 0.28;
        renderer.render(scene, camera);
      };
      tick();
    }
  }

  if (!customElements.get('moni-core')) customElements.define('moni-core', MoniCore);
})();
