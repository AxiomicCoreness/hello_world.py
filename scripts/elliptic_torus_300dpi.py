import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# --- A14 Bionic profile -----------------------------------------------------
matplotlib.rcParams.update({
    "figure.dpi": 300, "savefig.dpi": 300,
    "figure.facecolor": "black", "axes.facecolor": "black",
    "text.color": "white",
})

R, r = 2.0, 0.65          # major / minor radii — large ring, thin tube
U, V = np.meshgrid(np.linspace(0, 2*np.pi, 90),
                   np.linspace(0, 2*np.pi, 48))
X = (R + r*np.cos(V)) * np.cos(U)
Y = (R + r*np.cos(V)) * np.sin(U)
Z = r * np.sin(V)

fig = plt.figure(figsize=(10, 8), dpi=300, facecolor="black")
ax  = fig.add_subplot(111, projection="3d", facecolor="black")

# 1) cyan torus wireframe
ax.plot_wireframe(X, Y, Z, color="#7fffd4", linewidth=0.30,
                  alpha=0.55, rstride=2, cstride=2)

# 2) red equator — outer great circle, thin
t = np.linspace(0, 2*np.pi, 600)
ax.plot((R + r)*np.cos(t), (R + r)*np.sin(t), 0*t,
        color="#ff1a1a", linewidth=2.4, alpha=0.95)

# 3) yellow (2,3) torus knot — the marked cycle
p, q = 2, 3
s = np.linspace(0, 2*np.pi, 1200)
ax.plot((R + r*np.cos(q*s))*np.cos(p*s),
        (R + r*np.cos(q*s))*np.sin(p*s),
        r*np.sin(q*s), color="#ffe100", linewidth=2.0, alpha=0.95)

# 4) white lattice sample points (12 around equator, as in source)
theta = np.linspace(0, 2*np.pi, 12, endpoint=False)
ax.scatter((R + r)*np.cos(theta), (R + r)*np.sin(theta),
           np.zeros_like(theta), color="white", s=26,
           depthshade=False, edgecolors="none")

# 5) G marker at s = pi  (matches ~right-of-centre position in thumbnail)
sg = np.pi
gx = (R + r*np.cos(q*sg))*np.cos(p*sg)
gy = (R + r*np.cos(q*sg))*np.sin(p*sg)
gz = r*np.sin(q*sg)
ax.scatter([gx], [gy], [gz], color="#00ff66", s=60,
           depthshade=False, edgecolors="none")
ax.text(gx + 0.06, gy + 0.06, gz - 0.05, "G",
        color="#00ff66", fontsize=13, fontweight="bold")

# 6) two yellow orientation arrows from a nearby lattice point
ax_s = 2.55
axx = (R + r*np.cos(q*ax_s))*np.cos(p*ax_s)
axy = (R + r*np.cos(q*ax_s))*np.sin(p*ax_s)
axz = r*np.sin(q*ax_s)
# arrow 1: upward/right
ax.quiver(axx, axy, axz, 0.35, 0.18, 0.42,
          color="#ffe100", linewidth=1.8, arrow_length_ratio=0.30)
# arrow 2: forward/right, shorter
ax.quiver(axx, axy, axz, 0.55, -0.10, 0.10,
          color="#ffe100", linewidth=1.8, arrow_length_ratio=0.28)

# 7) equation, rotated 90° on the left
fig.text(0.028, 0.50, r"$y^{2} = x^{3} + Ax + B$",
         rotation=90, va="center", ha="left",
         color="white", fontsize=22,
         fontfamily="serif", fontstyle="italic")

# --- finalize ---------------------------------------------------------------
ax.set_axis_off()
ax.view_init(elev=24, azim=-62)
ax.set_box_aspect((1, 1, 0.42))
lim = R + r + 0.45
ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_zlim(-1.4, 1.4)

plt.tight_layout()
plt.savefig("elliptic_torus_300dpi.png", dpi=300,
            facecolor="black", bbox_inches="tight", pad_inches=0.04)
print("✅ rendered elliptic_torus_300dpi.png  (300 dpi, black bg)")
