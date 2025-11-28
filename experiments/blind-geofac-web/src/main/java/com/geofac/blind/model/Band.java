package com.geofac.blind.model;

import java.math.BigInteger;

public record Band(BigInteger start, BigInteger end, BigInteger center, String source, double score) {
}
