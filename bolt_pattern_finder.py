import json

import arguably
import numpy as np
import plotly.graph_objects as go


def get_closest_fractional(num, max_frac=5):
    closest_frac = 0
    quotient = 0

    fractional_part = num - np.floor(num)
    min_diff = np.inf

    for pow in range(max_frac + 1):
        this_diff = fractional_part % (0.5 ** pow)
        if this_diff < min_diff:
            min_diff = this_diff
            closest_frac = pow
            quotient = int(fractional_part // (0.5 ** pow))

    if quotient == 0:
        return f"{int(num)}"

    return f"{int(num)} {quotient}/{2 ** closest_frac}"


@arguably.command
def main(n_particles:int=1000, *, n_iterations=1_000_000, annealing_rate=0.99, save_to="bolt_pattern.json"):
    holes = {ltr: idx for (idx, ltr) in enumerate("ABCDEFGH")}

    # Symmetric matrix that represents distances between pairs of holes
    # Units are mm
    lengths = np.array([
        [  0.0000,  58.0000, 201.6125, 255.5875, 347.6625, 342.9000, 329.4063, 266.7000],
        [ 58.0000,   0.0000, 151.5000, 213.5188, 339.7250, 357.1875, 333.3750, 304.0063],
        [201.6125, 151.5000,   0.0000,  75.0000, 270.6687, 336.5500, 363.5375, 355.6000],
        [255.5875, 213.5188,  75.0000,   0.0000, 211.9313, 296.0688, 345.2813, 347.6625],
        [347.6625, 339.7250, 270.6687, 211.9313,   0.0000, 119.0000, 219.0750, 254.0000],
        [342.9000, 357.1875, 336.5500, 296.0688, 119.0000,   0.0000, 111.0000, 160.3375],
        [329.4063, 333.3750, 363.5375, 345.2813, 219.0750, 111.0000,   0.0000,  53.7500],
        [266.7000, 304.0063, 355.6000, 347.6625, 254.0000, 160.3375,  53.7500,   0.0000]
    ])

    # Now, let's find the positions of these holes. We'll start with a shitty
    # first guess, and descend from there. With 8 holes, we're exploring a 16D
    # space here.
    particles = np.random.uniform(
        0.0, np.max(lengths), (n_particles, lengths.shape[0], 2))
    particles[:, holes["A"], 0] = 0.0
    particles[:, holes["A"], 1] = 0.0
    particles[:, holes["H"], 1] = 0.0
    
    noise = 100.0
    scores = []
    noise_array = []
    for _ in range(n_iterations):
        best_particle, score = evaluate(particles, lengths)
        scores.append(score)
        noise_array.append(noise)

        # Now fuzz
        particles = np.random.normal(
            best_particle, noise, (n_particles, lengths.shape[0], 2)
        )
        particles[:, holes["A"], 0] = 0.0
        particles[:, holes["A"], 1] = 0.0
        particles[:, holes["H"], 1] = 0.0
        noise *= annealing_rate

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=scores))
    fig.add_trace(go.Scatter(y=noise_array))
    fig.show(renderer='browser')

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=best_particle[:, 0],
            y=best_particle[:, 1],
            line={"width": 0}
        )
    )
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    fig.show(renderer="browser")

    # Save the best particle
    with open(save_to, 'w') as fh:
        json.dump(
            {
                hole: [float(f"{c:.4f}") for c in best_particle[hole_idx]]
                for (hole, hole_idx) in holes.items()
            },
            fh,
            indent="    "
        )


def evaluate(particles: np.ndarray, lengths_mm: np.ndarray):
    x_diffs = particles[:, None, :, 0] - particles[:, :, None, 0]
    y_diffs = particles[:, None, :, 1] - particles[:, :, None, 1]
    particle_dists = (x_diffs ** 2.0 + y_diffs ** 2.0) ** 0.5

    # we'll use a simple L2 norm
    particle_scores = np.sum(
        (lengths_mm - particle_dists) ** 2.0, axis=(1, 2)) / 48
    
    min_idx = np.nanargmin(particle_scores)
    return particles[min_idx], particle_scores[min_idx]


if __name__ == "__main__":
    arguably.run()