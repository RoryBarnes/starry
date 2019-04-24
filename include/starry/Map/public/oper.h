/**
Reset the map coefficients, the axis, 
and all cached variables.

*/
inline void reset () 
{
    // Reset Ylms
    y.setZero();
    setY00();

    // Reset the filter
    f.setZero();
    // If there's no filter, set it to `pi`, which
    // (because of the 1/pi starry Ylm normalization)
    // ensures there's no effect on the flux or intensity
    if (fdeg == 0)
        f(0) = pi<Scalar>();

    // Reset limb darkening
    u.setZero();
    setU0();

    // Reset the axis
    inc = 90.0;
    obl = 0.0;
}

/**
Rotate the map *in place* by an angle `theta`.

*/
template <typename U=S>
inline EnableIf<!U::Temporal, void> rotate (
    const Scalar& theta
) 
{
    Scalar theta_rad = theta * radian;
    auto y_in = y;
    W.rotate(y_in, cos(theta_rad), sin(theta_rad), y);
}

/**
Rotate the map *in place* by an angle `theta`.

*/
template <typename U=S>
inline EnableIf<U::Temporal, void> rotate (
    const Scalar& theta
) 
{
    Scalar theta_rad = theta * radian;
    Matrix<Scalar> y_in = Eigen::Map<Matrix<Scalar>>(y.data(), Ny, Nt);
    Eigen::Map<Matrix<Scalar>> y_out = 
        Eigen::Map<Matrix<Scalar>>(y.data(), Ny, Nt);
    W.rotate(y_in, cos(theta_rad), sin(theta_rad), y_out);
}


/**
Add a gaussian spot at a given latitude/longitude on the map.

*/
inline void addSpot (
    const RowVector<Scalar>& amp,
    const Scalar& sigma,
    const Scalar& lat=0,
    const Scalar& lon=0,
    int l=-1
) {
    // Basic degree is max degree
    if (l < 0) 
        l = ydeg;
    if (l > ydeg) 
        throw std::invalid_argument("Invalid value for the map degree.");

    // Check `amp` dims
    if (amp.cols() != Nw * Nt)
        throw std::invalid_argument("Argument `amp` has the wrong shape.");

    // Compute the integrals recursively
    Vector<Scalar> IP(l + 1);
    Vector<Scalar> ID(l + 1);
    Matrix<Scalar> coeff(Ny, Nw);
    coeff.setZero();

    // Constants
    Scalar a = 1.0 / (2 * sigma * sigma);
    Scalar sqrta = sqrt(a);
    Scalar erfa = erf(2 * sqrta);
    Scalar term = exp(-4 * a);

    // Seeding values
    IP(0) = root_pi<Scalar>() / (2 * sqrta) * erfa;
    IP(1) = (root_pi<Scalar>() * sqrta * erfa + term - 1) / (2 * a);
    ID(0) = 0;
    ID(1) = IP(0);

    // Recurse
    int sgn = -1;
    for (int n = 2; n < l + 1; ++n) {
        IP(n) = (2.0 * n - 1.0) / (2.0 * n * a) * (ID(n - 1) + sgn * term - 1.0) +
                (2.0 * n - 1.0) / n * IP(n - 1) - (n - 1.0) / n * IP(n - 2);
        ID(n) = (2.0 * n - 1.0) * IP(n - 1) + ID(n - 2);
        sgn *= -1;
    }

    // Compute the coefficients of the expansion
    // normalized so the integral over the sphere is `amp`
    for (int n = 0; n < l + 1; ++n)
        coeff.row(n * n + n) = 0.25 * amp * sqrt(2 * n + 1) * (IP(n) / IP(0));

    // Rotate the spot to the correct lat/lon
    // \todo Speed this up with a single compound rotation
    Scalar lat_rad = lat * radian;
    Scalar lon_rad = lon * radian;
    rotateByAxisAngle(xhat<Scalar>(), cos(lat_rad), -sin(lat_rad), coeff);
    rotateByAxisAngle(yhat<Scalar>(), cos(lon_rad), sin(lon_rad), coeff);

    // Add this to the map
    if (S::Temporal) {
        for (int i = 1; i < Nt; ++i) {
            y.block(i * Ny, 0, Ny, 1) += coeff.col(i);
        }
    } else {
        y += coeff;
    }
    
}

/**
Generate a random isotropic map with a given power spectrum.

*/
template <typename V, typename U=S>
inline EnableIf<!(U::Spectral || U::Temporal), void> random (
    const Vector<Scalar>& power,
    const V& seed
) {
    randomInternal(power, seed, 0);
}

/**
Generate a random isotropic map with a given power spectrum.
NOTE: If `col = -1`, sets all columns to the same map.

*/
template <typename V, typename U=S>
inline EnableIf<(U::Spectral || U::Temporal), void> random (
    const Vector<Scalar>& power,
    const V& seed,
    int col=-1
) {
    randomInternal(power, seed, col);
}