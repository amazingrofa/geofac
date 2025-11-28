package com.geofac.blind.model;

import java.math.BigInteger;

public record Candidate(BigInteger d, double score, String source) {
}
