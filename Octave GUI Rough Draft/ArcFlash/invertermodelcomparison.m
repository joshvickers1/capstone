%% Arc Flash Inverter Modeling Comparison
% Demonstrates how different inverter models approximate arcing current
% relative to a theoretical (physics-based) inverter response

clear; clc; close all;

%% Time vector (arc duration)
t = linspace(0, 0.1, 2000);   % 100 ms window (typical inverter trip time)

%% Base parameters
I_rated = 100;      % Rated inverter current (A)
I_limit = 1.2 * I_rated;   % Inverter current limit
V_nom = 480;        % Nominal voltage (V)
R_internal = 0.15;  % Equivalent internal resistance (ohms)

%% -------------------------------
% THEORETICAL ARCING CURRENT MODEL
% -------------------------------
% Represents real inverter behavior:
% - Fast rise
% - Current-limited
% - Voltage-dependent decay
% - Arc self-extinguishing tendency

tau_rise = 0.002;    % Fast electronic response (2 ms)
tau_decay = 0.015;   % Control & protection decay (15 ms)

I_theoretical = I_limit ...
    .* (1 - exp(-t / tau_rise)) ...
    .* exp(-t / tau_decay);

%% ---------------------------------------
% MODEL 1: Voltage-Dependent Current Source
% ---------------------------------------
% Approximates inverter control reasonably well

V_arc = V_nom * exp(-t / 0.01);   % Arc voltage collapse
I_vdcs = I_limit .* (V_arc / V_nom);

%% ---------------------------------
% MODEL 2: Constant Current Source
% ---------------------------------
% Assumes fixed current until trip

trip_time = 0.04;  % 40 ms inverter trip
I_ccs = I_limit * ones(size(t));
I_ccs(t > trip_time) = 0;

%% ----------------------------------------
% MODEL 3: Voltage Behind Resistance (VBR)
% ----------------------------------------
% "Reasonable but incorrect" Thevenin model
% Still overestimates arc current for inverters

I_vbr_peak = 5 * I_rated;   % 5 pu fault current (typical misuse)
tau_vbr = 0.03;             % Faster decay than rotating machines

I_vbr = I_vbr_peak * exp(-t / tau_vbr);


%% ----------------
% Plot the results
% ----------------
figure('Color','w','Position',[100 100 900 500])
hold on; grid on;

plot(t*1000, I_theoretical, 'k', 'LineWidth', 3)
plot(t*1000, I_vdcs, '--b', 'LineWidth', 2)
plot(t*1000, I_ccs, ':r', 'LineWidth', 2)
plot(t*1000, I_vbr, '-.m', 'LineWidth', 2)

xlabel('Time (ms)')
ylabel('Arcing Current (A)')
title('Arc-Flash Arcing Current Modeling for Inverter-Based Sources')

legend( ...
    'Theoretical Inverter Response (Reference)', ...
    'Voltage-Dependent Current Source (VDCS)', ...
    'Constant Current Source (CCS)', ...
    'Voltage Behind Resistance (VBR)', ...
    'Location','northeast')

ylim([0 max(I_vbr)*1.05])

%% -------------------------------
% Error metrics (model accuracy)
% -------------------------------
err_vdcs = trapz(t, abs(I_theoretical - I_vdcs));
err_ccs  = trapz(t, abs(I_theoretical - I_ccs));
err_vbr  = trapz(t, abs(I_theoretical - I_vbr));

fprintf('\nIntegrated Absolute Error (lower = better):\n');
fprintf('VDCS: %.2f A·s\n', err_vdcs);
fprintf('CCS : %.2f A·s\n', err_ccs);
fprintf('VBR : %.2f A·s\n', err_vbr);
