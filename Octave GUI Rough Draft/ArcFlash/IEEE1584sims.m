clear; clc; close all;


Voc = 5;              % System voltage (kV)
G = 25;               % Electrode gap (mm)
D = 300;              % Working distance (mm)
config = 'VCB';       % Configuration (Vertical Conductors in Box)
Cf = 1.0;             % Configuration factor (approx 1.0–1.5 typical)

% Coefficients for arcing current model (representative)
k1 = -0.153; k2 = 0.983; k3 = 0.004;

% Incident energy equation coefficients (IEEE-like)
K = -0.792;
nI = 1.081;    % exponent on I_arc
nT = 1.000;    % exponent on time
nD = -1.473;   % exponent on distance


Ibf_vec = linspace(1, 65, 80);       % Bolted fault current [kA]
t_vec   = linspace(0.01, 0.5, 60);   % Arc duration [s]

E_mat   = zeros(length(Ibf_vec), length(t_vec)); % Energy [cal/cm²]
AFB_mat = zeros(size(E_mat));                    % Arc Flash Boundary [mm]


for i = 1:length(Ibf_vec)
    Ibf = Ibf_vec(i);
    for j = 1:length(t_vec)
        t = t_vec(j);

        % Step 1: Arcing current [kA]
        logIarc = k1 + k2*log10(Ibf) + k3*log10(G);
        Iarc = 10^(logIarc);

        % Step 2: Incident energy (IEEE 1584-2018 style)
        logE = K + nI*log10(Iarc) + nT*log10(t) + nD*log10(D) + log10(Cf);
        E = 10^(logE);          % J/cm²
        E_cal = E / 4.184;      % convert to cal/cm²
        E_mat(i,j) = E_cal;

        % Step 3: Arc flash boundary (approx for 1.2 cal/cm²)
        E_limit = 1.2; % cal/cm² threshold
        AFB = D * sqrt(E_cal / E_limit);
        AFB_mat(i,j) = AFB;
    end
end



%Incident Energy vs Fault Current (different clearing times)
figure;
t_sel = [0.02, 0.1, 0.3];
hold on;
for k = 1:length(t_sel)
    [~, idx] = min(abs(t_vec - t_sel(k)));
    plot(Ibf_vec, E_mat(:, idx), 'LineWidth', 1.8, ...
         'DisplayName', sprintf('t = %.0f ms', t_sel(k)*1000));
end
xlabel('Bolted Fault Current I_{bf} (kA)');
ylabel('Incident Energy (cal/cm^2)');
title('Incident Energy vs Fault Current');
legend show; grid on; hold off;

% Arc Flash Boundary vs Fault Current
figure;
hold on;
for k = 1:length(t_sel)
    [~, idx] = min(abs(t_vec - t_sel(k)));
    plot(Ibf_vec, AFB_mat(:, idx), 'LineWidth', 1.8, ...
         'DisplayName', sprintf('t = %.0f ms', t_sel(k)*1000));
end
xlabel('Bolted Fault Current I_{bf} (kA)');
ylabel('Arc Flash Boundary (mm)');
title('Arc Flash Boundary vs Fault Current');
legend show; grid on; hold off;

% Incident Energy vs Arc Duration
figure;
Ibf_sel = [5, 20, 50];
hold on;
for k = 1:length(Ibf_sel)
    [~, idx] = min(abs(Ibf_vec - Ibf_sel(k)));
    plot(t_vec * 1000, E_mat(idx, :), 'LineWidth', 1.8, ...
         'DisplayName', sprintf('I_{bf} = %.0f kA', Ibf_sel(k)));
end
xlabel('Arc Duration t (ms)');
ylabel('Incident Energy (cal/cm^2)');
title('Incident Energy vs Arc Duration');
legend show; grid on; hold off;

disp('Simulation complete — 2-D plots generated.');
