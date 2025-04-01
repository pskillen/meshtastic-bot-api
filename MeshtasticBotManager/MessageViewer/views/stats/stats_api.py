"""API endpoints for retrieving packet statistics."""

from datetime import datetime, timedelta

from django.db.models import ExpressionWrapper, F, BigIntegerField, Sum, Window, Case, When, Value, BooleanField, Q
from django.db.models.functions import Lag, TruncHour, Coalesce

import dateutil.parser
from PacketLogging.models import LocalStatsPacket
from rest_framework import status, viewsets
from rest_framework.response import Response


class StatsViewSet(viewsets.GenericViewSet):
    """ViewSet for retrieving packet statistics."""

    def list(self, request):
        """Get packet statistics for the specified time range."""
        start_date = request.query_params.get("startDate")
        end_date = request.query_params.get("endDate")
        node_id = request.query_params.get("nodeId")
        channel = request.query_params.get("channel")

        # Parse the dates if provided
        if start_date:
            try:
                start_date = dateutil.parser.isoparse(start_date)
            except ValueError:
                return Response({"error": "Invalid startDate format"}, status=status.HTTP_400_BAD_REQUEST)
        if end_date:
            try:
                end_date = dateutil.parser.isoparse(end_date)
            except ValueError:
                return Response({"error": "Invalid endDate format"}, status=status.HTTP_400_BAD_REQUEST)

        # ensure we're selecting sensible date ranges
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if start_date and end_date:
            if start_date > end_date:
                return Response({"error": "startDate must be before endDate"}, status=status.HTTP_400_BAD_REQUEST)
        # can't select more than 30 days
        if start_date and end_date:
            if (end_date - start_date).days > 30:
                return Response({"error": "Date range must be less than 30 days"}, status=status.HTTP_400_BAD_REQUEST)

        # Base query
        queryset = LocalStatsPacket.objects.all()

        # Apply filters
        if node_id:
            queryset = queryset.filter(from_int=node_id)
        if channel:
            queryset = queryset.filter(channel=channel)
        if start_date:
            queryset = queryset.filter(time__gte=start_date)
        if end_date:
            queryset = queryset.filter(time__lte=end_date)

        # Get hourly stats with window functions for differences
        hourly_stats = (
            queryset.annotate(
                hour=TruncHour("time"),
                prev_tx=Window(expression=Lag("numPacketsTx"), order_by=F("time").asc()),
                prev_rx=Window(expression=Lag("numPacketsRx"), order_by=F("time").asc()),
                prev_rx_bad=Window(expression=Lag("numPacketsRxBad"), order_by=F("time").asc()),
                prev_rx_dupe=Window(expression=Lag("numRxDupe"), order_by=F("time").asc()),
            )
            .values("hour")
            .annotate(
                packets_tx=Case(
                    When(
                        Q(numPacketsTx__lt=F("prev_tx")),
                        then=F("numPacketsTx")
                    ),
                    default=ExpressionWrapper(F("numPacketsTx") - F("prev_tx"), output_field=BigIntegerField())
                ),
                packets_rx=Case(
                    When(
                        Q(numPacketsRx__lt=F("prev_rx")),
                        then=F("numPacketsRx")
                    ),
                    default=ExpressionWrapper(F("numPacketsRx") - F("prev_rx"), output_field=BigIntegerField())
                ),
                packets_rx_bad=Case(
                    When(
                        Q(numPacketsRxBad__lt=F("prev_rx_bad")),
                        then=F("numPacketsRxBad")
                    ),
                    default=ExpressionWrapper(F("numPacketsRxBad") - F("prev_rx_bad"), output_field=BigIntegerField())
                ),
                packets_rx_dupe=Case(
                    When(
                        Q(numRxDupe__lt=F("prev_rx_dupe")),
                        then=F("numRxDupe")
                    ),
                    default=ExpressionWrapper(F("numRxDupe") - F("prev_rx_dupe"), output_field=BigIntegerField())
                ),
            )
            .order_by("hour")
        )

        # Calculate summary
        summary = {
            "total_packets_tx": queryset.aggregate(total=Sum("numPacketsTx"))["total"] or 0,
            "total_packets_rx": queryset.aggregate(total=Sum("numPacketsRx"))["total"] or 0,
            "total_packets_rx_bad": queryset.aggregate(total=Sum("numPacketsRxBad"))["total"] or 0,
            "total_packets_rx_dupe": queryset.aggregate(total=Sum("numRxDupe"))["total"] or 0,
            "time_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }

        # Format response
        response = {
            "hourly_stats": [
                {
                    "timestamp": stat["hour"].isoformat(),
                    "packets_tx": stat["packets_tx"] or 0,
                    "packets_rx": stat["packets_rx"] or 0,
                    "packets_rx_bad": stat["packets_rx_bad"] or 0,
                    "packets_rx_dupe": stat["packets_rx_dupe"] or 0,
                    "total_packets": (
                        (stat["packets_tx"] or 0)
                        + (stat["packets_rx"] or 0)
                        + (stat["packets_rx_bad"] or 0)
                        + (stat["packets_rx_dupe"] or 0)
                    ),
                }
                for stat in hourly_stats
            ],
            "summary": summary,
        }

        return Response(response, status=status.HTTP_200_OK)
